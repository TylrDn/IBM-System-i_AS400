"""Command-line payroll uploader."""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass

from colorama import init
from dotenv import load_dotenv

from ibmi_transfer import (
    call_program_via_ftp_rcmd,
    call_program_via_ssh,
    upload_csv_via_ftp,
    upload_csv_via_sftp,
)
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
    use_ssh: bool


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
        use_ssh=os.environ.get("USE_SSH", "1") == "1",
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
    if cfg.use_ssh:
        upload_csv_via_sftp(
            cfg.host, cfg.user, cfg.password, cfg.csv_file, cfg.remote_dir
        )
        cmd = f"system 'CALL PGM({cfg.lib}/{cfg.program})'"
        logger.info("Running remote program via SSH")
        call_program_via_ssh(cfg.host, cfg.user, cmd, os.environ.get("SSH_KEY"))
    else:
        upload_csv_via_ftp(
            cfg.host, cfg.user, cfg.password, cfg.csv_file, cfg.remote_dir, use_tls=True
        )
        logger.info("Running remote program via FTP RCMD over TLS")
        call_program_via_ftp_rcmd(
            cfg.host, cfg.user, cfg.password, cfg.lib, cfg.program, use_tls=True
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
