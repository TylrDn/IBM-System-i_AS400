"""Tests for payroll_b module."""

# ruff: noqa: S101,S106,S108

import argparse
from functools import partial

import payroll_b


def _cfg(lib: str = "LIB", program: str = "PROG") -> payroll_b.Config:
    return payroll_b.Config(
        host="h",
        user="u",
        password="p",
        remote_dir="/tmp",
        lib=lib,
        program=program,
        csv_file="file.csv",
    )


def _args() -> argparse.Namespace:
    return argparse.Namespace(dry_run=False, verbose=False)


def _noop(*args, **kwargs):  # noqa: ANN001 - match external signature
    return None


def test_main_returns_nonzero_on_failure(monkeypatch):
    monkeypatch.setattr(payroll_b, "parse_args", _args)
    monkeypatch.setattr(payroll_b, "load_config", _cfg)
    monkeypatch.setattr(payroll_b, "csv_from_excel", _noop)
    monkeypatch.setattr(payroll_b, "upload_csv_via_sftp", _noop)

    def boom(*args, **kwargs):  # noqa: ANN001 - match external signature
        raise RuntimeError("fail")

    monkeypatch.setattr(payroll_b, "call_program_via_ssh", boom)
    assert payroll_b.main() == 1


def test_main_rejects_invalid_library(monkeypatch):
    monkeypatch.setattr(payroll_b, "parse_args", _args)
    monkeypatch.setattr(payroll_b, "load_config", partial(_cfg, lib="BAD-LIB"))
    monkeypatch.setattr(payroll_b, "csv_from_excel", _noop)
    monkeypatch.setattr(payroll_b, "upload_csv_via_sftp", _noop)
    monkeypatch.setattr(payroll_b, "call_program_via_ssh", _noop)
    try:
        payroll_b.main()
    except ValueError as exc:  # noqa: PT011 - expect exception
        assert "Invalid library" in str(exc)
    else:  # pragma: no cover - safety net
        raise AssertionError("invalid library should raise")
