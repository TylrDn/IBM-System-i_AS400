import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1]))

import ibmi_transfer  # noqa: E402


def test_upload_csv_via_sftp(monkeypatch, tmp_path):
    class FakeSFTP:
        def __init__(self):
            self.put_calls = []

        def put(self, local, remote):
            self.put_calls.append((local, remote))

        def close(self):
            raise NotImplementedError()

    class FakeSSHClient:
        last = None

        def __init__(self, *args, **kwargs):
            FakeSSHClient.last = self

        def set_missing_host_key_policy(self, policy):
            raise NotImplementedError()

        def load_system_host_keys(self):
            raise NotImplementedError()

        def connect(self, host, username, password):
            self.host = host
            self.username = username
            self.password = password

        def open_sftp(self):
            self.sftp = FakeSFTP()
            return self.sftp

        def close(self):
            raise NotImplementedError()

    monkeypatch.setattr(ibmi_transfer, "paramiko", SimpleNamespace(SSHClient=FakeSSHClient, RejectPolicy=object))
    local = tmp_path / "sample.csv"
    local.write_text("hello")
    remote_dir = tmp_path.as_posix()
    ibmi_transfer.upload_csv_via_sftp("h", "u", "p", local, remote_dir)
    client = FakeSSHClient.last
    expected = [(str(local), f"{remote_dir}/{local.name}")]
    if client.sftp.put_calls != expected:  # nosec - used for test validation
        raise AssertionError(f"Unexpected put calls: {client.sftp.put_calls}")


def test_call_program_via_ssh(monkeypatch):
    class FakeFile:
        def __init__(self):
            self.channel = type("C", (), {"recv_exit_status": staticmethod(lambda: 0)})()

        @staticmethod
        def read():
            return b""

    class FakeClient:
        last = None

        def __init__(self):
            FakeClient.last = self

        def load_system_host_keys(self):
            raise NotImplementedError()

        def set_missing_host_key_policy(self, policy):
            raise NotImplementedError()

        def connect(self, host, username, key_filename=None):
            self.host = host
            self.username = username
            self.key_filename = key_filename

        def exec_command(self, command):
            self.command = command
            f = FakeFile()
            return f, f, FakeFile()

        def close(self):
            raise NotImplementedError()

    monkeypatch.setattr(
        ibmi_transfer,
        "paramiko",
        SimpleNamespace(SSHClient=FakeClient, RejectPolicy=object),
    )
    ibmi_transfer.call_program_via_ssh("h", "u", "cmd", key_path="k")
    client = FakeClient.last
    if client.command != "cmd":  # nosec - used for test validation
        raise AssertionError(f"Unexpected command: {client.command}")
    if client.key_filename != "k":  # nosec - used for test validation
        raise AssertionError(f"Unexpected key: {client.key_filename}")
