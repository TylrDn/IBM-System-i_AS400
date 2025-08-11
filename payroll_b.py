"""Wrapper script for payroll utilities."""

import logging
import os

from colorama import init
from dotenv import load_dotenv

from ibmi_transfer import (
    call_program_via_ftp_rcmd,
    call_program_via_ssh,
    upload_csv_via_ftp,
)
from payroll_utils import csv_from_excel


if __name__ == "__main__":
    load_dotenv()
    init()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    csv_from_excel()

    host = os.environ["HOST"]
    user = os.environ["USER"]
    password = os.environ.get("PASSWORD", "")
    remote_dir = os.environ.get("REMOTE_DIR", "/tmp")
    lib = os.environ.get("LIB", "")
    program = os.environ.get("PROGRAM", "")
    csv_file = os.environ.get("CSV_FILE", "Data_EO.csv")
    use_ssh = os.environ.get("USE_SSH", "0") == "1"

    logger.info("Uploading %s to %s", csv_file, remote_dir)
    upload_csv_via_ftp(host, user, password, csv_file, remote_dir)

    if use_ssh:
        cmd = f"system 'CALL PGM({lib}/{program})'"
        logger.info("Running remote program via SSH")
        call_program_via_ssh(host, user, cmd, os.environ.get("SSH_KEY"))
    else:
        logger.info("Running remote program via FTP RCMD")
        call_program_via_ftp_rcmd(host, user, password, lib, program)
