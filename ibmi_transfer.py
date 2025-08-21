"""Utilities for transferring files and invoking programs on IBM i.

This module provides pure-Python helpers for uploading payroll CSV files
and executing IBM i programs over secure channels. Only encrypted network
protocols are used to avoid leaking credentials or data in transit.
"""

from __future__ import annotations

import os
import re
import shlex
from pathlib import Path
from typing import Optional

import paramiko

_SAFE_PATH = re.compile(r"^[A-Za-z0-9_./-]+$")
_SAFE_HOST = re.compile(r"^[A-Za-z0-9_.-]+$")


class TransferError(RuntimeError):
    """Raised when a network command returns a non-success status."""


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
        try:
            client = paramiko.SSHClient()
            try:
                client.load_system_host_keys()
                client.set_missing_host_key_policy(paramiko.RejectPolicy())
            except NotImplementedError:
                # Some client implementations may not support host key functions
                pass
            client.connect(host, username=user, password=password)
            sftp = client.open_sftp()
            path = Path(local_path)
            sftp.put(str(path), f"{remote_dir}/{path.name}")
            try:
                sftp.close()
            except NotImplementedError:
                pass
            try:
                client.close()
            except NotImplementedError:
                pass
            return
        except Exception as exc:  # pragma: no cover - network dependent
            if attempt == retries:
                raise TransferError(f"SFTP upload failed: {exc}") from exc


def call_program_via_ssh(
    host: str,
    user: str,
    cmd: str | list[str],
    key_path: Optional[str] = None,
) -> None:
    """Run *cmd* on *host* via ``ssh`` using ``paramiko``."""

    if not _SAFE_HOST.match(host) or not _SAFE_HOST.match(user):
        raise ValueError("Unsafe host or user")

    if isinstance(cmd, str):
        args = shlex.split(cmd)
    else:
        args = list(cmd)
    for arg in args:
        if not _SAFE_PATH.match(arg):
            raise ValueError(f"Unsafe command argument: {arg}")
    command = " ".join(shlex.quote(arg) for arg in args)

    client = paramiko.SSHClient()
    try:
        try:
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        except NotImplementedError:
            pass
        client.connect(host, username=user, key_filename=key_path)
        stdin, stdout, stderr = client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        _ = stdout.read().decode()
        err = stderr.read().decode()
    finally:
        try:
            client.close()
        except NotImplementedError:
            pass
    if exit_status != 0:
        raise RuntimeError(
            f"SSH command failed with exit code {exit_status}: {err}"
        )
    return None

