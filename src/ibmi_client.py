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
_SFTP_CLIENT_NOT_CONNECTED = "SFTP client not connected"


def _sanitize_parts(cmd: str | Iterable[str]) -> list[str]:
    """Split *cmd* and ensure it contains no unsafe shell characters."""
    if isinstance(cmd, str):
        if _UNSAFE_SEP.search(cmd):
            raise ValueError("Unsafe shell command")
        parts = shlex.split(cmd)
    else:
        parts = list(cmd)
    if not parts:
        raise ValueError("Empty command")
    for part in parts:
        if _UNSAFE_SEP.search(part) or not _SAFE_PATH.match(part):
            raise ValueError("Unsafe shell command")
    return parts


class IBMiClient:
    """Thin SSH/SFTP wrapper around paramiko."""

    def __init__(self, config, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.client: paramiko.SSHClient | None = None
        self.sftp: paramiko.SFTPClient | None = None
        self.log = logging.getLogger(__name__)

    def __enter__(self):
        """Enter the context manager, establishing a connection."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        """Exit the context manager, ensuring the connection is closed."""
        self.close()

    @timed
    def connect(self) -> None:
        """Establish SSH and SFTP connections."""
        if self.dry_run:
            self.log.info("DRY-RUN connect to %s", self.config.host)
            return
        self.client = paramiko.SSHClient()
        try:
            self.client.load_system_host_keys()
        except NotImplementedError:
            pass
        try:
            policy = (
                paramiko.AutoAddPolicy()
                if getattr(self.config, "allow_auto_hostkey", False)
                else paramiko.RejectPolicy()
            )
            self.client.set_missing_host_key_policy(policy)
        except NotImplementedError:
            # Older paramiko versions on some platforms may not implement
            # host key handling; continue without overriding the default
            pass
        kwargs = {"hostname": self.config.host, "username": self.config.user}
        key = getattr(self.config, "ssh_key", None)
        pw = getattr(self.config, "password", None)
        if key:
            kwargs["key_filename"] = key
        elif pw:
            kwargs["password"] = pw
        try:
            self.client.connect(**kwargs)
            self.sftp = self.client.open_sftp()
        except NotImplementedError:
            # Allow tests or minimal paramiko implementations that raise
            # NotImplementedError for unimplemented network calls.
            self.sftp = None

    def close(self) -> None:
        """Close any active SSH or SFTP connections."""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()

    @timed
    def ssh_run(
        self, cmd: str | Iterable[str], timeout: int = 60
    ) -> tuple[str, str, int]:
        """Execute *cmd* on the remote host via SSH."""
        self.log.info("SSH: %s", cmd)
        if self.dry_run:
            return "", "", 0
        if not self.client:
            raise RuntimeError("SSH client not connected")
        parts = _sanitize_parts(cmd)
        safe_cmd = " ".join(shlex.quote(part) for part in parts)
        _, stdout, stderr = self.client.exec_command(  # nosec B601
            safe_cmd, timeout=timeout
        )
        out = stdout.read().decode("utf-8", "ignore")
        err = stderr.read().decode("utf-8", "ignore")
        rc = stdout.channel.recv_exit_status()
        if rc != 0:
            self.log.error("Command failed rc=%s stderr=%s", rc, err.strip())
        return out, err, rc

    @timed
    def sftp_put(self, local: Path, remote: str) -> None:
        """Upload *local* file to *remote* path via SFTP."""
        self.log.info("PUT %s -> %s", local, remote)
        if self.dry_run:
            return
        if not self.sftp:
            raise RuntimeError(_SFTP_CLIENT_NOT_CONNECTED)
        self.sftp.put(str(local), remote)

    @timed
    def sftp_get(self, remote: str, local: Path) -> None:
        """Download *remote* file to *local* path via SFTP."""
        self.log.info("GET %s -> %s", remote, local)
        if self.dry_run:
            return
        if not self.sftp:
            raise RuntimeError(_SFTP_CLIENT_NOT_CONNECTED)
        self.sftp.get(remote, str(local))

    def _ensure_dir(self, path: str) -> None:
        """Create *path* on the remote host if it does not exist."""
        if not self.sftp:
            raise RuntimeError(_SFTP_CLIENT_NOT_CONNECTED)
        if not _SAFE_PATH.match(path):
            raise ValueError(f"Unsafe remote path: {path}")
        self.log.info("Ensure remote dir %s", path)
        parts = path.strip("/").split("/")
        cur = "/" if path.startswith("/") else ""
        for part in parts:
            cur = f"{cur}/{part}" if cur and not cur.endswith("/") else f"{cur}{part}"
            try:
                self.sftp.stat(cur)
            except IOError:
                self.sftp.mkdir(cur)

    @timed
    def ensure_remote_dirs(self, paths: Iterable[str]) -> None:
        """Ensure each directory in *paths* exists on the remote host."""
        if self.dry_run:
            for p in paths:
                self.log.info("DRY-RUN mkdir -p %s", p)
            return
        for p in paths:
            self._ensure_dir(p)
