import csv
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from payroll_utils import csv_from_excel


def test_xls_to_csv(tmp_path):
    xls = Path(__file__).resolve().parents[1] / "Data_EO.xls"
    out = tmp_path / "out.csv"
    csv_from_excel(str(xls), str(out))
    with out.open() as fh:
        rows = list(csv.reader(fh))
    assert rows[0][0].strip() == "0090"
    assert rows[0][1] == "916.05"
