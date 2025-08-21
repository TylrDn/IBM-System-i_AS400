"""Tests for IBM i client helper."""

# ruff: noqa: S101

import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import src.ibmi_client as ibmi_client_mod  # noqa: E402
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


def test_connect_uses_reject_policy(monkeypatch) -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.policy = None

        def load_system_host_keys(self) -> None:
            raise NotImplementedError()

        def set_missing_host_key_policy(
            self, policy
        ) -> None:  # noqa: ANN001 - external API
            self.policy = policy

        def connect(self, **kwargs) -> None:  # noqa: ANN003 - external API
            raise NotImplementedError()

        @staticmethod
        def open_sftp():  # noqa: ANN001 - external API
            return None

        def close(self) -> None:
            raise NotImplementedError()

    fake_paramiko = types.SimpleNamespace(
        SSHClient=FakeClient,
        AutoAddPolicy=lambda: "auto",
        RejectPolicy=lambda: "reject",
    )
    monkeypatch.setattr(ibmi_client_mod, "paramiko", fake_paramiko)
    cfg = types.SimpleNamespace(host="h", user="u", allow_auto_hostkey=False)
    client = IBMiClient(cfg)
    client.connect()
    assert client.client.policy == "reject"


def test_connect_allows_auto_hostkey(monkeypatch) -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.policy = None

        def load_system_host_keys(self) -> None:
            raise NotImplementedError()

        def set_missing_host_key_policy(
            self, policy
        ) -> None:  # noqa: ANN001 - external API
            self.policy = policy

        def connect(self, **kwargs) -> None:  # noqa: ANN003 - external API
            raise NotImplementedError()

        @staticmethod
        def open_sftp():  # noqa: ANN001 - external API
            return None

        def close(self) -> None:
            raise NotImplementedError()

    fake_paramiko = types.SimpleNamespace(
        SSHClient=FakeClient,
        AutoAddPolicy=lambda: "auto",
        RejectPolicy=lambda: "reject",
    )
    monkeypatch.setattr(ibmi_client_mod, "paramiko", fake_paramiko)
    cfg = types.SimpleNamespace(host="h", user="u", allow_auto_hostkey=True)
    client = IBMiClient(cfg)
    client.connect()
    assert client.client.policy == "auto"
