import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from payroll_utils import csv_from_excel  # noqa: E402


def test_xls_to_csv(tmp_path):
    xls = Path(__file__).resolve().parents[1] / "examples" / "payroll_sample.xlsx"
    if not xls.exists():
        pytest.skip("sample XLSX not available")
    out = tmp_path / "out.csv"
    csv_from_excel(str(xls), str(out))
    with out.open() as fh:
        rows = list(csv.reader(fh))
    if rows[0][0].strip() != "1001":  # nosec - test validation
        raise AssertionError("Unexpected employee ID")
    if rows[0][1] != "1234.56":  # nosec - test validation
        raise AssertionError("Unexpected amount")
