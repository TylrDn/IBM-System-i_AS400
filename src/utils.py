import csv
import hashlib
import logging
import os
import time
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Callable

import pandas as pd
from dotenv import load_dotenv


def setup_logger(level: int = logging.INFO) -> None:
    """Configure root logger."""
    logging.basicConfig(
        level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )


def timed(fn: Callable) -> Callable:
    """Decorator logging execution time of functions."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            return fn(*args, **kwargs)
        finally:
            duration = time.time() - start
            logging.getLogger(fn.__module__).debug(
                "%s took %.2fs", fn.__name__, duration
            )

    return wrapper


def sniff_csv(path: Path) -> type[csv.Dialect]:
    """Sniff CSV dialect and normalise to UTF-8 LF."""
    data = path.read_text(encoding="utf-8")
    path.write_text(data.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")
    sample = data[:1024]
    return csv.Sniffer().sniff(sample)


@timed
def xlsx_to_csv(in_xlsx: Path, out_csv: Path) -> Path:
    """Convert XLSX to CSV using pandas."""
    df = pd.read_excel(in_xlsx)
    df.to_csv(out_csv, index=False, line_terminator="\n")
    return out_csv


def sha256_file(path: Path) -> str:
    """Return SHA-256 digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class Config:
    host: str
    user: str
    ssh_key: str | None
    password: str | None
    lib_stg: str
    ifs_dir: str
    jobq: str
    outq: str
    allow_auto_hostkey: bool = False


def load_config(env_file: str = ".env") -> Config:
    """Load configuration from .env file."""
    load_dotenv(env_file)
    host = os.getenv("IBMI_HOST")
    user = os.getenv("IBMI_USER")
    ssh_key = os.getenv("IBMI_SSH_KEY")
    password = os.getenv("IBMI_PASSWORD")
    lib_stg = os.getenv("LIB_STG")
    ifs_dir = os.getenv("IFS_STAGING_DIR")
    jobq = os.getenv("JOBQ", "QSYSNOMAX")
    outq = os.getenv("OUTQ", "QPRINT")
    allow = os.getenv("ALLOW_AUTO_HOSTKEY", "false").lower() == "true"
    if not all([host, user, lib_stg, ifs_dir]):
        raise ValueError("Missing required config keys")
    cfg = Config(host, user, ssh_key, password, lib_stg, ifs_dir, jobq, outq, allow)
    return cfg
