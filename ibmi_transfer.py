"""Utilities for transferring files and invoking programs on IBM i.

This module provides pure-Python helpers for uploading payroll CSV files
and executing IBM i programs over FTP or SSH. Network operations are kept
simple to ease mocking in tests."""

from __future__ import annotations

import ftplib
import os
import subprocess
from pathlib import Path
from typing import Iterable, Optional


class FTPError(RuntimeError):
    """Raised when an FTP command returns a non-success status."""


def upload_csv_via_ftp(
    host: str,
    user: str,
    password: str,
    local_path: str | os.PathLike[str],
    remote_dir: str,
    use_tls: bool = False,
) -> str:
    """Upload *local_path* to *remote_dir* on the IBM i server.

    Returns the server response from the ``STOR`` command.
    """

    ftp_class = ftplib.FTP_TLS if use_tls else ftplib.FTP
    ftp = ftp_class()
    try:
        ftp.connect(host, 21)
        ftp.login(user, password)
        if use_tls and isinstance(ftp, ftplib.FTP_TLS):
            ftp.prot_p()
        ftp.cwd(remote_dir)
        path = Path(local_path)
        with path.open("rb") as handle:
            resp = ftp.storbinary(f"STOR {path.name}", handle)
        if not resp.startswith("226") and not resp.startswith("250"):
            raise FTPError(resp)
        ftp.quit()
        return resp
    finally:
        try:
            ftp.close()
        except Exception:
            pass


def call_program_via_ftp_rcmd(
    host: str,
    user: str,
    password: str,
    lib: str,
    program: str,
    parms: Iterable[str] | None = None,
    use_tls: bool = False,
) -> str:
    """Invoke an IBM i program using the FTP ``QUOTE RCMD`` command."""

    ftp_class = ftplib.FTP_TLS if use_tls else ftplib.FTP
    ftp = ftp_class()
    try:
        ftp.connect(host, 21)
        ftp.login(user, password)
        if use_tls and isinstance(ftp, ftplib.FTP_TLS):
            ftp.prot_p()
        cmd = f"RCMD CALL PGM({lib}/{program})"
        if parms:
            parm_str = " ".join(parms)
            cmd += f" PARM({parm_str})"
        resp = ftp.sendcmd(f"QUOTE {cmd}")
        if not resp.startswith("2"):
            raise FTPError(resp)
        ftp.quit()
        return resp
    finally:
        try:
            ftp.close()
        except Exception:
            pass


def call_program_via_ssh(
    host: str,
    user: str,
    cmd: str,
    key_path: Optional[str] = None,
) -> subprocess.CompletedProcess[str]:
    """Run *cmd* on *host* via ``ssh`` and return the completed process."""

    ssh_cmd = ["ssh"]
    if key_path:
        ssh_cmd.extend(["-i", key_path])
    ssh_cmd.append(f"{user}@{host}")
    ssh_cmd.append(cmd)
    proc = subprocess.run(ssh_cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(
            proc.returncode, ssh_cmd, output=proc.stdout, stderr=proc.stderr
        )
    return proc
