import argparse

import argparse

import payroll_b


def _cfg(lib="LIB", program="PROG"):
    return payroll_b.Config(
        host="h",
        user="u",
        password="p",
        remote_dir="/tmp",
        lib=lib,
        program=program,
        csv_file="file.csv",
    )


def test_main_returns_nonzero_on_failure(monkeypatch):
    monkeypatch.setattr(payroll_b, "parse_args", lambda: argparse.Namespace(dry_run=False, verbose=False))
    monkeypatch.setattr(payroll_b, "load_config", lambda: _cfg())
    monkeypatch.setattr(payroll_b, "csv_from_excel", lambda: None)
    monkeypatch.setattr(payroll_b, "upload_csv_via_sftp", lambda *args, **kwargs: None)

    def boom(*args, **kwargs):  # noqa: ANN001 - match external signature
        raise RuntimeError("fail")

    monkeypatch.setattr(payroll_b, "call_program_via_ssh", boom)
    assert payroll_b.main() == 1


def test_main_rejects_invalid_library(monkeypatch):
    monkeypatch.setattr(payroll_b, "parse_args", lambda: argparse.Namespace(dry_run=False, verbose=False))
    monkeypatch.setattr(payroll_b, "load_config", lambda: _cfg(lib="BAD-LIB"))
    monkeypatch.setattr(payroll_b, "csv_from_excel", lambda: None)
    monkeypatch.setattr(payroll_b, "upload_csv_via_sftp", lambda *args, **kwargs: None)
    monkeypatch.setattr(payroll_b, "call_program_via_ssh", lambda *args, **kwargs: None)
    try:
        payroll_b.main()
    except ValueError as exc:  # noqa: PT011 - expect exception
        assert "Invalid library" in str(exc)
    else:  # pragma: no cover - safety net
        assert False, "invalid library should raise"
