import hashlib
import logging
import sys
from pathlib import Path
import hashlib
import logging
import sys
from pathlib import Path
import types
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

import src.utils as utils  # noqa: E402


def test_setup_logger(caplog):
    utils.setup_logger(logging.DEBUG)
    with caplog.at_level(logging.DEBUG):
        logging.getLogger(__name__).debug("msg")
    assert "msg" in caplog.text


def test_timed_decorator(monkeypatch, caplog):
    import itertools

    counter = itertools.count()

    def _mock_time():
        try:
            return next(counter)
        except StopIteration:
            return 0

    monkeypatch.setattr(utils.time, "time", _mock_time)

    @utils.timed
    def sample(x):
        return x * 2

    with caplog.at_level(logging.DEBUG):
        assert sample(3) == 6
    assert "sample took" in caplog.text


def test_sniff_csv_normalises(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("a,b\r\nc,d\re,f")
    dialect = utils.sniff_csv(p)
    assert dialect.delimiter == ","
    assert p.read_text() == "a,b\nc,d\ne,f"


def test_xlsx_to_csv(monkeypatch, tmp_path):
    df = types.SimpleNamespace(to_csv=lambda path, index=False, line_terminator="\n": Path(path).write_text("x"))
    monkeypatch.setattr(utils.pd, "read_excel", lambda path: df)
    out = utils.xlsx_to_csv(Path("in.xlsx"), tmp_path / "out.csv")
    assert out.read_text() == "x"


def test_sha256_file_success(tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("hello")
    assert (
        utils.sha256_file(f)
        == hashlib.sha256(b"hello").hexdigest()
    )


def test_sha256_file_not_file(tmp_path):
    with pytest.raises(ValueError):
        utils.sha256_file(tmp_path)


def test_load_config_success(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(
        "IBMI_HOST=h\nIBMI_USER=u\nLIB_STG=l\nIFS_STAGING_DIR=/ifs\n"
    )
    for key in ("IBMI_HOST", "IBMI_USER", "LIB_STG", "IFS_STAGING_DIR"):
        monkeypatch.delenv(key, raising=False)
    cfg = utils.load_config(str(env))
    assert cfg.host == "h"
    assert cfg.jobq == "QSYSNOMAX"


def test_load_config_missing(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("IBMI_HOST=h\n")
    for key in ("IBMI_USER", "LIB_STG", "IFS_STAGING_DIR"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ValueError):
        utils.load_config(str(env))
