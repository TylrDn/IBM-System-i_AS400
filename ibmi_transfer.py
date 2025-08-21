"""Utilities for transferring files and invoking programs on IBM i.

This module provides pure-Python helpers for uploading payroll CSV files
and executing IBM i programs over secure channels. Only encrypted network
protocols are used to avoid leaking credentials or data in transit.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Optional

import paramiko

_SAFE_PATH = re.compile(r"^[A-Za-z0-9_./-]+$")


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
    for attempt in range(1, retries + 1):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, username=user, password=password)
            sftp = client.open_sftp()
            path = Path(local_path)
            sftp.put(str(path), f"{remote_dir}/{path.name}")
            sftp.close()
            client.close()
            return
        except Exception as exc:  # pragma: no cover - network dependent
            if attempt == retries:
                raise TransferError(f"SFTP upload failed: {exc}") from exc


def call_program_via_ssh(
    host: str,
    user: str,
    cmd: str,
    key_path: Optional[str] = None,
    *,
    raw: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run *cmd* on *host* via ``ssh`` and return the completed process."""

    ssh_cmd = ["ssh"]
    if key_path:
        ssh_cmd.extend(["-i", key_path])
    ssh_cmd.append(f"{user}@{host}")
    if raw:
        ssh_cmd.append(cmd)
    else:
        ssh_cmd.extend(shlex.split(cmd))

    try:
        return subprocess.run(ssh_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"SSH command failed with exit code {exc.returncode}: {exc.stderr}"
        ) from exc

