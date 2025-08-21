import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))


def test_sql_files_are_fully_qualified() -> None:
    root = Path("ibmi")
    setup = (root / "setup.sql").read_text().upper()
    apply = (root / "apply.sql").read_text().upper()
    teardown = (root / "teardown.sql").read_text().upper()

    for content in (setup, apply):
        assert "&LIB_STG." in content
        assert "SET SCHEMA" not in content

    assert "DROP SCHEMA IF EXISTS &LIB_STG" in teardown
