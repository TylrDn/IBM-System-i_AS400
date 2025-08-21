import logging
import re
import shlex
from pathlib import Path
from typing import Iterable

import paramiko

from .utils import timed

_SAFE_PATH = re.compile(r"^[A-Za-z0-9_./-]+$")
# Block common shell separators including newlines to avoid command injection
_UNSAFE_SEP = re.compile(r"[;&|\r\n]")


class IBMiClient:
    """Thin SSH/SFTP wrapper around paramiko."""

    def __init__(self, config, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.client: paramiko.SSHClient | None = None
        self.sftp: paramiko.SFTPClient | None = None
        self.log = logging.getLogger(__name__)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    @timed
    def connect(self) -> None:
        if self.dry_run:
            self.log.info("DRY-RUN connect to %s", self.config.host)
            return
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        if self.config.allow_auto_hostkey:
            # Warn rather than automatically trusting unknown hosts
            self.client.set_missing_host_key_policy(paramiko.WarningPolicy())
        kwargs = {"hostname": self.config.host, "username": self.config.user}
        if self.config.ssh_key:
            kwargs["key_filename"] = self.config.ssh_key
        elif self.config.password:
            kwargs["password"] = self.config.password
        self.client.connect(**kwargs)
        self.sftp = self.client.open_sftp()

    def close(self) -> None:
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()

    @timed
    def ssh_run(self, cmd: str, timeout: int = 60) -> tuple[str, str, int]:
        self.log.info("SSH: %s", cmd)
        if self.dry_run:
            return "", "", 0
        if not self.client:
            raise RuntimeError("SSH client not connected")
        if _UNSAFE_SEP.search(cmd):
            raise ValueError("Unsafe shell command")
        # Sanitize the command by quoting each argument to avoid shell injection
        parts = shlex.split(cmd)
        safe_cmd = " ".join(shlex.quote(part) for part in parts)
        _, stdout, stderr = self.client.exec_command(safe_cmd, timeout=timeout)
        out = stdout.read().decode("utf-8", "ignore")
        err = stderr.read().decode("utf-8", "ignore")
        rc = stdout.channel.recv_exit_status()
        if rc != 0:
            self.log.error("Command failed rc=%s stderr=%s", rc, err.strip())
        return out, err, rc

    @timed
    def sftp_put(self, local: Path, remote: str) -> None:
        self.log.info("PUT %s -> %s", local, remote)
        if self.dry_run:
            return
        if not self.sftp:
            raise RuntimeError("SFTP client not connected")
        self.sftp.put(str(local), remote)

    @timed
    def sftp_get(self, remote: str, local: Path) -> None:
        self.log.info("GET %s -> %s", remote, local)
        if self.dry_run:
            return
        if not self.sftp:
            raise RuntimeError("SFTP client not connected")
        self.sftp.get(remote, str(local))

    @timed
    def ensure_remote_dirs(self, paths: Iterable[str]) -> None:
        if self.dry_run:
            for p in paths:
                self.log.info("DRY-RUN mkdir -p %s", p)
            return
        if not self.sftp:
            raise RuntimeError("SFTP client not connected")
        for p in paths:
            if not _SAFE_PATH.match(p):
                raise ValueError(f"Unsafe remote path: {p}")
            self.log.info("Ensure remote dir %s", p)
            # Recursively create each path component to mimic `mkdir -p`
            parts = p.strip("/").split("/")
            cur = "/" if p.startswith("/") else ""
            for part in parts:
                cur = f"{cur}/{part}" if cur and not cur.endswith("/") else f"{cur}{part}"
                try:
                    self.sftp.stat(cur)
                except IOError:
                    self.sftp.mkdir(cur)
