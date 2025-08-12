"""Utilities for transferring files and invoking programs on IBM i.

This module provides pure-Python helpers for uploading payroll CSV files
and executing IBM i programs over FTP or SSH. Network operations are kept
simple to ease mocking in tests."""

from __future__ import annotations

import ftplib
import os
import shlex
import subprocess
from pathlib import Path
from typing import Iterable, Optional

import paramiko


class FTPError(RuntimeError):
    """Raised when a network command returns a non-success status."""


def upload_csv_via_ftp(
    host: str,
    user: str,
    password: str,
    local_path: str | os.PathLike[str],
    remote_dir: str,
    *,
    use_tls: bool = True,
    retries: int = 3,
) -> str:
    """Upload *local_path* to *remote_dir* on the IBM i server using FTP/FTPS."""

    for attempt in range(1, retries + 1):
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
            if not resp.startswith(("226", "250")):
                raise FTPError(resp)
            ftp.quit()
            return resp
        except Exception as exc:
            if attempt == retries:
                raise FTPError(f"FTP upload failed: {exc}")
        finally:
            try:
                ftp.close()
            except Exception:
                pass
    raise FTPError("FTP upload failed")


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
        except Exception as exc:
            if attempt == retries:
                raise FTPError(f"SFTP upload failed: {exc}")
    raise FTPError("SFTP upload failed")


def call_program_via_ftp_rcmd(
    host: str,
    user: str,
    password: str,
    lib: str,
    program: str,
    parms: Iterable[str] | None = None,
    *,
    use_tls: bool = True,
    retries: int = 3,
) -> str:
    """Invoke an IBM i program using the FTP ``QUOTE RCMD`` command."""

    for attempt in range(1, retries + 1):
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
        except Exception as exc:
            if attempt == retries:
                raise FTPError(f"FTP RCMD failed: {exc}")
        finally:
            try:
                ftp.close()
            except Exception:
                pass
    raise FTPError("FTP RCMD failed")


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
