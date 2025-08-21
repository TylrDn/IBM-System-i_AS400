import logging
import sys
from pathlib import Path
import types
import pytest
import builtins

sys.path.append(str(Path(__file__).resolve().parents[1]))

import payroll_utils  # noqa: E402


def test_open_sheet_success(monkeypatch):
    class FakeBook:
        def sheet_by_index(self, idx):
            return "sheet"

    monkeypatch.setattr(payroll_utils.xlrd, "open_workbook", lambda f: FakeBook())
    sheet = payroll_utils._open_sheet("file.xls")
    assert sheet == "sheet"


def test_open_sheet_file_missing(monkeypatch, caplog):
    def fake_open(path):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(payroll_utils.xlrd, "open_workbook", fake_open)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(FileNotFoundError):
            payroll_utils._open_sheet("bad.xls")
        assert "Opening the bad.xls file failed" in caplog.text


def test_open_sheet_xlrd_error(monkeypatch, caplog):
    def fake_open(path):
        raise payroll_utils.xlrd.biffh.XLRDError("boom")

    monkeypatch.setattr(payroll_utils.xlrd, "open_workbook", fake_open)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(payroll_utils.xlrd.biffh.XLRDError):
            payroll_utils._open_sheet("bad.xls")
        assert "Failed to open bad.xls" in caplog.text


def test_write_sheet_to_csv_success(tmp_path):
    class Sheet:
        nrows = 2

        def row_values(self, row):
            return [row, row + 1]

    csv_file = tmp_path / "out.csv"
    count = payroll_utils._write_sheet_to_csv(Sheet(), csv_file.as_posix())
    assert count == 2
    assert csv_file.read_text().strip().splitlines()[0] == "0,1"


def test_write_sheet_to_csv_oserror(monkeypatch, tmp_path, caplog):
    class Sheet:
        nrows = 1

        def row_values(self, row):
            return [1]

    def fake_open(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(builtins, "open", fake_open)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(OSError):
            payroll_utils._write_sheet_to_csv(Sheet(), (tmp_path / "out.csv").as_posix())
        assert "Failed to write to CSV file" in caplog.text


def test_csv_from_excel_success(monkeypatch):
    monkeypatch.setattr(payroll_utils, "_open_sheet", lambda f: "sheet")
    called = {}

    def fake_write(sheet, csv_file):
        called["args"] = (sheet, csv_file)
        return 1

    monkeypatch.setattr(payroll_utils, "_write_sheet_to_csv", fake_write)
    payroll_utils.csv_from_excel("in.xls", "out.csv")
    assert called["args"] == ("sheet", "out.csv")


def test_csv_from_excel_missing_paths(monkeypatch):
    monkeypatch.setattr(payroll_utils.os, "getenv", lambda *a, **k: None)
    with pytest.raises(ValueError):
        payroll_utils.csv_from_excel(None, None)
