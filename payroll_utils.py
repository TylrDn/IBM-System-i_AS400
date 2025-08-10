"""Utility functions for payroll data processing and FTP upload.

This module consolidates logic previously duplicated across multiple scripts
and provides a single implementation that can be reused by any entrypoint.
"""

import csv
import logging
import subprocess
import sys
from ftplib import FTP, all_errors

import xlrd
from decouple import config
from colorama import Fore, init

# start colorama and configure basic logging
init()
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

FTP_TIMEOUT = None


def csv_from_excel(xls_file: str = "Data_EO.xls", csv_file: str = "Data_EO.csv") -> None:
    """Read *xls_file* and write its contents to *csv_file*.

    Parameters
    ----------
    xls_file: str, optional
        Source Excel file name. Defaults to ``Data_EO.xls``.
    csv_file: str, optional
        Destination CSV file name. Defaults to ``Data_EO.csv``.
    """

    counter = 0
    try:
        workbook = xlrd.open_workbook(xls_file)
        sheet = workbook.sheet_by_index(0)
    except FileNotFoundError:
        logger.error(
            Fore.RED
            + f"Opening the {xls_file} file failed, please make sure that the file exists in the folder."
        )
        sys.exit(1)

    with open(csv_file, "w", newline="") as csv_handle:
        writer = csv.writer(csv_handle, quoting=csv.QUOTE_NONNUMERIC)
        for row in range(sheet.nrows):
            writer.writerow(sheet.row_values(row))
            counter += 1
            logger.info(f"{sheet.row_values(row)}")

    logger.info(Fore.GREEN + f"Total records in the csv file ------> {counter}")


def ftp_upload(file_transfer_name: str = "./Data_EO.csv") -> None:
    """Upload the generated CSV to the IBM i server and run post-processing."""

    ftp = FTP()
    logger.info("")
    try:
        logger.info(
            Fore.YELLOW
            + "Establishing connection with IBM i Server (AS/400), please wait..."
        )
        ftp.connect(config("Host"), 21, timeout=FTP_TIMEOUT)
        ftp.login(config("user"), config("password"))
        logger.info(Fore.GREEN + f"Connection established with ==> {ftp.getwelcome()}")

        ftp.cwd("/tmp")

        # Transfer CSV file to the IBM i IFS folder
        with open(file_transfer_name, "rb") as csv_file:
            ftp.storlines("STORE Data_EO.csv", csv_file)
            logger.info(f"Transferred {file_transfer_name}")

        ftp.quit()

        # Call the interface to connect to IBM i via FTP and invoke update programs
        subprocess.run("ftp_cl_as400.bat", check=True)

        # Successfully completed process
        subprocess.run("python payroll_process_done.py", check=True)

    except all_errors as err:
        logger.error(
            Fore.RED
            + f"FTP error communicating with server {config('Host')}: {err}"
        )
        raise
    except subprocess.CalledProcessError as err:
        logger.error(Fore.RED + f"Subprocess failed: {err}")
        raise
    finally:
        try:
            ftp.close()
        except all_errors as exc:
            logger.error(f"Error closing FTP connection: {exc}")

