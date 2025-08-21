import logging
import sys
import types
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

import src.workflow as wf  # noqa: E402


def test_ensure_safe():
    assert wf._ensure_safe("abc_123", "f") == "abc_123"
    with pytest.raises(ValueError):
        wf._ensure_safe("bad;rm", "f")


def test_remote_dirs():
    assert wf._remote_dirs("/ifs")[-1] == "/ifs/scripts"


def test_prepare_csv(monkeypatch, tmp_path):
    src = tmp_path / "input.xlsx"
    src.write_text("dummy")
    csv_path = tmp_path / "input.csv"
    called = {"xlsx": False, "sniff": False, "sha": False}
    monkeypatch.setattr(wf, "xlsx_to_csv", lambda i, o: called.__setitem__("xlsx", True) or csv_path)
    monkeypatch.setattr(wf, "sniff_csv", lambda p: called.__setitem__("sniff", True))
    monkeypatch.setattr(wf, "sha256_file", lambda p: called.__setitem__("sha", True) or "digest")
    out = wf._prepare_csv(src, logging.getLogger(__name__))
    assert out == csv_path
    assert all(called.values())


def test_sync_scripts(tmp_path):
    puts = []

    class Client:
        def sftp_put(self, local, remote):
            puts.append((local, remote))

    wf._sync_scripts(Client(), "/ifs")
    assert (Path("ibmi") / "setup.sql", "/ifs/scripts/setup.sql") in puts


def test_run_setup_and_submit_job():
    cmds = []

    class Client:
        def ssh_run(self, cmd):
            cmds.append(cmd)

    wf._run_setup(Client(), "/ifs", "LIB")
    wf._submit_job(Client(), "LIB", "/ifs", "OUTQ", "JOBQ")
    assert any("RUNSQLSTM" in c for c in cmds)
    assert any("SBMJOB" in c for c in cmds)


def test_find_status_file(monkeypatch):
    class Client:
        def __init__(self):
            self.calls = 0
            self.sftp = types.SimpleNamespace(listdir=self.listdir)

        def listdir(self, path):
            self.calls += 1
            return [] if self.calls < 2 else ["done.status"]

    times = iter([0, 1, 2])
    monkeypatch.setattr(wf.time, "time", lambda: next(times))
    status = wf._find_status_file(Client(), "dir", 5)
    assert status == "done.status"


def test_find_status_file_timeout(monkeypatch):
    client = types.SimpleNamespace(sftp=types.SimpleNamespace(listdir=lambda p: []))
    times = iter([0, 1, 2, 3, 20])
    monkeypatch.setattr(wf.time, "time", lambda: next(times))
    with pytest.raises(TimeoutError):
        wf._find_status_file(client, "dir", 10)


def test_fetch_result(tmp_path):
    class Client:
        def sftp_get(self, remote, local):
            Path(local).write_text("data")

    wf._fetch_result(Client(), "/ifs", tmp_path / "file.csv", logging.getLogger(__name__))
    assert (Path("outputs") / "file_result.csv").exists()


def test_fetch_result_warning(caplog, tmp_path):
    class Client:
        def sftp_get(self, remote, local):
            raise RuntimeError("fail")

    with caplog.at_level(logging.WARNING):
        wf._fetch_result(Client(), "/ifs", tmp_path / "file.csv", logging.getLogger(__name__))
        assert "Could not fetch result" in caplog.text


def test_wait_for_marker_success(monkeypatch, tmp_path):
    monkeypatch.setattr(wf, "_find_status_file", lambda c, d, e: "ok.status")

    class Client:
        def __init__(self):
            self.gets = []

        def sftp_get(self, remote, local):
            self.gets.append((remote, local))
            Path(local).write_text("OK")

    fetched = []
    monkeypatch.setattr(wf, "_fetch_result", lambda c, d, p, l: fetched.append(True))
    wf._wait_for_marker(Client(), "/ifs", tmp_path / "in.csv", fetch_outputs=True, log=logging.getLogger(__name__), timeout=0)
    assert fetched


def test_wait_for_marker_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(wf, "_find_status_file", lambda c, d, e: "bad.status")

    class Client:
        def sftp_get(self, remote, local):
            Path(local).write_text("FAILED cause")

    with pytest.raises(RuntimeError):
        wf._wait_for_marker(Client(), "/ifs", tmp_path / "in.csv", fetch_outputs=False, log=logging.getLogger(__name__), timeout=0)


def test_run_workflow(monkeypatch, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a")
    monkeypatch.setattr(wf, "_prepare_csv", lambda src, log: csv_path)
    monkeypatch.setattr(wf, "_wait_for_marker", lambda *a, **k: None)
    actions = []

    class Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            pass

        def ensure_remote_dirs(self, dirs):
            actions.append(("dirs", dirs))

        def sftp_put(self, local, remote):
            actions.append(("put", local, remote))

        def ssh_run(self, cmd):
            actions.append(("ssh", cmd))

    monkeypatch.setattr(wf, "IBMiClient", lambda cfg, dry_run=False: Client())
    cfg = types.SimpleNamespace(ifs_dir="/ifs", lib_stg="L", outq="O", jobq="J")
    wf.run_workflow(csv_path, cfg, sync=False, fetch_outputs=False, timeout=0, dry_run=True)
    assert any(op[0] == "put" for op in actions)


def test_run_workflow_sync(monkeypatch, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a")
    monkeypatch.setattr(wf, "_prepare_csv", lambda src, log: csv_path)
    monkeypatch.setattr(wf, "_wait_for_marker", lambda *a, **k: None)
    sync_called = []
    monkeypatch.setattr(wf, "_sync_scripts", lambda c, d: sync_called.append(d))

    class Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            pass

        def ensure_remote_dirs(self, dirs):
            pass

        def sftp_put(self, local, remote):
            pass

        def ssh_run(self, cmd):
            pass

    monkeypatch.setattr(wf, "IBMiClient", lambda cfg, dry_run=False: Client())
    cfg = types.SimpleNamespace(ifs_dir="/ifs", lib_stg="L", outq="O", jobq="J")
    wf.run_workflow(csv_path, cfg, sync=True, fetch_outputs=False, timeout=0, dry_run=True)
    assert sync_called == ["/ifs"]


def test_teardown(monkeypatch):
    cmds = []

    class Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            pass

        def ssh_run(self, cmd):
            cmds.append(cmd)

    monkeypatch.setattr(wf, "IBMiClient", lambda cfg, dry_run=False: Client())
    cfg = types.SimpleNamespace(ifs_dir="/ifs", lib_stg="L")
    wf.teardown(cfg, dry_run=True)
    assert any("teardown.sql" in c for c in cmds)
