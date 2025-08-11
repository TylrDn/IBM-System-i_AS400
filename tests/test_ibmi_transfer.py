from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from unittest import mock

import ibmi_transfer


def test_upload_csv_via_ftp(monkeypatch, tmp_path):
    class FakeFTP:
        last = None

        def __init__(self, *args, **kwargs):
            FakeFTP.last = self

        def connect(self, host, port):
            self.host = host

        def login(self, user, password):
            self.user = user
            self.password = password

        def cwd(self, path):
            self.path = path

        def storbinary(self, cmd, handle):
            self.cmd = cmd
            self.data = handle.read()
            return "226 OK"

        def quit(self):
            self.quit_called = True

        def close(self):
            pass

    monkeypatch.setattr(ibmi_transfer, "ftplib", SimpleNamespace(FTP=FakeFTP, FTP_TLS=FakeFTP))
    local = tmp_path / "sample.csv"
    local.write_text("hello")
    resp = ibmi_transfer.upload_csv_via_ftp("h", "u", "p", local, "/tmp")
    ftp = FakeFTP.last
    assert resp == "226 OK"
    assert ftp.path == "/tmp"
    assert ftp.cmd == f"STOR {local.name}"
    assert ftp.data == b"hello"


def test_call_program_via_ftp_rcmd(monkeypatch):
    class FakeFTP:
        last = None

        def __init__(self, *args, **kwargs):
            FakeFTP.last = self

        def connect(self, host, port):
            pass

        def login(self, user, password):
            pass

        def sendcmd(self, cmd):
            self.cmd = cmd
            return "250 OK"

        def quit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(ibmi_transfer, "ftplib", SimpleNamespace(FTP=FakeFTP, FTP_TLS=FakeFTP))
    resp = ibmi_transfer.call_program_via_ftp_rcmd("h", "u", "p", "LIB", "PGM", ["'A'"])
    ftp = FakeFTP.last
    assert resp == "250 OK"
    assert ftp.cmd == "QUOTE RCMD CALL PGM(LIB/PGM) PARM('A')"


def test_call_program_via_ssh(monkeypatch):
    called = {}

    def fake_run(cmd, capture_output, text):
        called["cmd"] = cmd
        return mock.Mock(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(ibmi_transfer.subprocess, "run", fake_run)
    ibmi_transfer.call_program_via_ssh("h", "u", "cmd", key_path="k")
    assert called["cmd"] == ["ssh", "-i", "k", "u@h", "cmd"]
