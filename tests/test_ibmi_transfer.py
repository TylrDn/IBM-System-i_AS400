import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.append(str(Path(__file__).resolve().parents[1]))

import ibmi_transfer  # noqa: E402


def test_upload_csv_via_sftp(monkeypatch, tmp_path):
    class FakeSFTP:
        def __init__(self):
            self.put_calls = []

        def put(self, local, remote):
            self.put_calls.append((local, remote))

        def close(self):
            pass

    class FakeSSHClient:
        last = None

        def __init__(self, *args, **kwargs):
            FakeSSHClient.last = self

        def set_missing_host_key_policy(self, policy):
            pass

        def load_system_host_keys(self):
            pass

        def connect(self, host, username, password):
            self.host = host
            self.username = username
            self.password = password

        def open_sftp(self):
            self.sftp = FakeSFTP()
            return self.sftp

        def close(self):
            pass

    monkeypatch.setattr(ibmi_transfer, "paramiko", SimpleNamespace(SSHClient=FakeSSHClient, RejectPolicy=object))
    local = tmp_path / "sample.csv"
    local.write_text("hello")
    ibmi_transfer.upload_csv_via_sftp("h", "u", "p", local, "/tmp")
    client = FakeSSHClient.last
    assert client.sftp.put_calls == [(str(local), f"/tmp/{local.name}")]  # nosec


def test_call_program_via_ssh(monkeypatch):
    called = {}

    def fake_run(cmd, capture_output, text, **kwargs):
        called["cmd"] = cmd
        called.update(kwargs)
        return mock.Mock(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(ibmi_transfer.subprocess, "run", fake_run)
    ibmi_transfer.call_program_via_ssh("h", "u", "cmd", key_path="k")
    assert called["cmd"] == ["ssh", "-i", "k", "u@h", "cmd"]  # nosec
    assert called.get("check") is True  # nosec
