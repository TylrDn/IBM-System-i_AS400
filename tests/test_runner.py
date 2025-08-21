import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import src.runner as runner  # noqa: E402


def test_parse_args(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["runner", "--file", "input.csv"])
    args = runner.parse_args()
    assert args.file == "input.csv"
    assert not args.sync


def test_main_runs_workflow(monkeypatch):
    args = types.SimpleNamespace(
        file="f.csv",
        sync=True,
        fetch_outputs=True,
        dry_run=False,
        timeout_seconds=1,
        jobq=None,
        outq=None,
        lib_stg=None,
        ifs_dir=None,
        teardown=False,
    )
    monkeypatch.setattr(runner, "parse_args", lambda: args)
    cfg = types.SimpleNamespace(jobq="J", outq="O", lib_stg="L", ifs_dir="/ifs")
    monkeypatch.setattr(runner, "load_config", lambda: cfg)
    called = {}

    def fake_run_workflow(path, cfg_obj, **opts):
        called["path"] = path
        called.update(opts)

    monkeypatch.setattr(runner, "run_workflow", fake_run_workflow)
    assert runner.main() == 0
    assert called["path"] == Path("f.csv")
    assert called["sync"]


def test_main_teardown(monkeypatch):
    args = types.SimpleNamespace(
        file="f.csv",
        sync=False,
        fetch_outputs=False,
        dry_run=True,
        timeout_seconds=5,
        jobq=None,
        outq=None,
        lib_stg=None,
        ifs_dir=None,
        teardown=True,
    )
    monkeypatch.setattr(runner, "parse_args", lambda: args)
    cfg = types.SimpleNamespace(jobq="J", outq="O", lib_stg="L", ifs_dir="/ifs")
    monkeypatch.setattr(runner, "load_config", lambda: cfg)
    called = {}

    def fake_teardown(cfg_arg, dry_run):
        called["cfg"] = cfg_arg
        called["dry_run"] = dry_run

    import src.workflow as wf

    monkeypatch.setattr(wf, "teardown", fake_teardown)
    assert runner.main() == 0
    assert called["dry_run"]


def test_main_error(monkeypatch):
    args = types.SimpleNamespace(
        file="f.csv",
        sync=False,
        fetch_outputs=False,
        dry_run=False,
        timeout_seconds=0,
        jobq=None,
        outq=None,
        lib_stg=None,
        ifs_dir=None,
        teardown=False,
    )
    monkeypatch.setattr(runner, "parse_args", lambda: args)

    def bad_config():
        raise RuntimeError("boom")

    monkeypatch.setattr(runner, "load_config", bad_config)
    assert runner.main() == 1
