"""Command-line payroll uploader."""

from __future__ import annotations

import argparse
import logging
import os
import re
from dataclasses import dataclass

from colorama import init
from dotenv import load_dotenv

from ibmi_transfer import call_program_via_ssh, upload_csv_via_sftp
from payroll_utils import csv_from_excel


@dataclass
class Config:
    host: str
    user: str
    password: str
    remote_dir: str
    lib: str
    program: str
    csv_file: str


def load_config() -> Config:
    load_dotenv()
    return Config(
        host=os.environ.get("HOST", ""),
        user=os.environ.get("USER", ""),
        password=os.environ.get("PASSWORD", ""),
        remote_dir=os.environ.get("REMOTE_DIR", "/tmp"),
        lib=os.environ.get("LIB", ""),
        program=os.environ.get("PROGRAM", ""),
        csv_file=os.environ.get("CSV_FILE", "examples/payroll_sample.csv"),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload payroll CSV to IBM i")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate without uploading"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s"
    )
    init()
    cfg = load_config()
    csv_from_excel()
    logger = logging.getLogger(__name__)
    if args.dry_run:
        logger.info("Dry run: would upload %s to %s", cfg.csv_file, cfg.remote_dir)
        return 0
    logger.info("Uploading %s to %s", cfg.csv_file, cfg.remote_dir)
    upload_csv_via_sftp(cfg.host, cfg.user, cfg.password, cfg.csv_file, cfg.remote_dir)
    if not re.fullmatch(r"[A-Za-z0-9_]+", cfg.lib):
        raise ValueError("Invalid library name")
    if not re.fullmatch(r"[A-Za-z0-9_]+", cfg.program):
        raise ValueError("Invalid program name")
    cmd = f"system 'CALL PGM({cfg.lib}/{cfg.program})'"
    logger.info("Running remote program via SSH")
    call_program_via_ssh(cfg.host, cfg.user, cmd, os.environ.get("SSH_KEY"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
