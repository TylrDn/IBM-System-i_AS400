import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from payroll_utils import _write_sheet_to_csv  # noqa: E402


class DummySheet:
    def __init__(self, rows):
        self.rows = rows
        self.nrows = len(rows)

    def row_values(self, idx):
        return self.rows[idx]


def test_formula_injection_neutralized(tmp_path):
    sheet = DummySheet([["=2+5"], ["@mal"], ["safe"]])
    out = tmp_path / "out.csv"
    _write_sheet_to_csv(sheet, str(out))
    with out.open() as fh:
        rows = [r[0] for r in csv.reader(fh)]
    assert rows[0].startswith("'") and rows[0][1:].startswith("=2+5")
    assert rows[1].startswith("'") and rows[1][1:].startswith("@mal")
    assert rows[2] == "safe"


def test_csv_output_readable(tmp_path):
    sheet = DummySheet([["val", 3.14]])
    out = tmp_path / "number.csv"
    _write_sheet_to_csv(sheet, str(out))
    with out.open() as fh:
        rows = list(csv.reader(fh))
    assert rows == [["val", "3.14"]]
