import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.ibmi_client import IBMiClient  # noqa: E402


def test_ssh_run_rejects_newlines() -> None:
    """ssh_run should block commands containing newlines."""
    client = IBMiClient(config=types.SimpleNamespace(), dry_run=False)
    # Provide a dummy client to satisfy connection check
    client.client = object()  # type: ignore[assignment]
    try:
        client.ssh_run("echo hi\nwhoami")
    except ValueError as exc:  # noqa: PT011 - expect exception
        assert "Unsafe shell command" in str(exc)
    else:  # pragma: no cover - safety net
        raise AssertionError("newline should be rejected")


def test_ensure_remote_dirs_creates_missing() -> None:
    """ensure_remote_dirs should create missing directories recursively."""

    class DummySFTP:
        def __init__(self) -> None:
            self.created: list[str] = []

        @staticmethod
        def stat(path: str) -> None:  # noqa: ANN001 - param signature fixed by API
            raise IOError()

        def mkdir(
            self, path: str
        ) -> None:  # noqa: ANN001 - param signature fixed by API
            self.created.append(path)

    client = IBMiClient(config=types.SimpleNamespace(), dry_run=False)
    client.sftp = DummySFTP()
    client.ensure_remote_dirs(["/a/b/c"])
    assert client.sftp.created == ["/a", "/a/b", "/a/b/c"]


def test_ensure_remote_dirs_rejects_unsafe() -> None:
    client = IBMiClient(config=types.SimpleNamespace(), dry_run=False)
    client.sftp = object()  # type: ignore[assignment]
    try:
        client.ensure_remote_dirs(["bad;rm"])
    except ValueError as exc:  # noqa: PT011 - expect exception
        assert "Unsafe remote path" in str(exc)
    else:  # pragma: no cover - safety net
        raise AssertionError("unsafe path should be rejected")
