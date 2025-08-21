"""Utilities for transferring files and invoking programs on IBM i.

This module provides pure-Python helpers for uploading payroll CSV files
and executing IBM i programs over secure channels. Only encrypted network
protocols are used to avoid leaking credentials or data in transit.
"""

from __future__ import annotations

import logging
import os
import re
import shlex
from pathlib import Path
from typing import Optional

import paramiko

_SAFE_PATH = re.compile(r"^[A-Za-z0-9_./-]+$")
_SAFE_HOST = re.compile(r"^[A-Za-z0-9_.-]+$")
# Block common shell separators including newlines to avoid command injection
_UNSAFE_SEP = re.compile(r"[;&|\r\n]")


def _sanitize_parts(cmd: str | list[str]) -> list[str]:
    """Split *cmd* and ensure it contains no unsafe shell characters."""
    if isinstance(cmd, str):
        if _UNSAFE_SEP.search(cmd):
            raise ValueError("Unsafe command")
        parts = shlex.split(cmd)
    else:
        parts = list(cmd)
    if not parts:
        raise ValueError("Empty command")
    for part in parts:
        if _UNSAFE_SEP.search(part) or not _SAFE_PATH.match(part):
            raise ValueError(f"Unsafe command argument: {part}")
    return parts


class TransferError(RuntimeError):
    """Raised when a network command returns a non-success status."""


def _init_client() -> paramiko.SSHClient:
    """Return an SSH client with host-key policies set."""
    client = paramiko.SSHClient()
    try:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
    except NotImplementedError:
        # Some client implementations may not support host key functions
        pass
    return client


def _safe_close(obj) -> None:
    """Attempt to close *obj*, logging but ignoring errors."""
    try:
        obj.close()
    except Exception as exc:  # pragma: no cover - best effort cleanup
        logging.getLogger(__name__).debug("close failed: %s", exc)


def upload_csv_via_sftp(
    host: str,
    user: str,
    password: str,
    local_path: str | os.PathLike[str],
    remote_dir: str,
    *,
    retries: int = 3,
) -> None:
    """Upload *local_path* to *remote_dir* on the IBM i server using SFTP."""

    if not _SAFE_PATH.match(remote_dir):
        raise ValueError("Unsafe remote directory")
    if not _SAFE_HOST.match(host) or not _SAFE_HOST.match(user):
        raise ValueError("Unsafe host or user")
    for attempt in range(1, retries + 1):
        client = _init_client()
        sftp = None
        try:
            client.connect(host, username=user, password=password)
            sftp = client.open_sftp()
            path = Path(local_path)
            sftp.put(str(path), f"{remote_dir}/{path.name}")
            return
        except Exception as exc:  # pragma: no cover - network dependent
            if attempt == retries:
                raise TransferError(f"SFTP upload failed: {exc}") from exc
        finally:
            if sftp:
                _safe_close(sftp)
            _safe_close(client)


def call_program_via_ssh(
    host: str,
    user: str,
    cmd: str | list[str],
    key_path: Optional[str] = None,
) -> None:
    """Run *cmd* on *host* via ``ssh`` using ``paramiko``."""

    if not _SAFE_HOST.match(host) or not _SAFE_HOST.match(user):
        raise ValueError("Unsafe host or user")

    args = _sanitize_parts(cmd)
    command = " ".join(shlex.quote(arg) for arg in args)

    client = _init_client()
    try:
        client.connect(host, username=user, key_filename=key_path)
        _, stdout, stderr = client.exec_command(command)  # nosec B601
        exit_status = stdout.channel.recv_exit_status()
        _ = stdout.read().decode()
        err = stderr.read().decode()
    finally:
        _safe_close(client)
    if exit_status != 0:
        raise RuntimeError(
            f"SSH command failed with exit code {exit_status}: {err}"
        )
    return None

