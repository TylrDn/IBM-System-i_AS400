"""Utility functions for payroll data processing and FTP upload.

This module consolidates logic previously duplicated across multiple scripts
and provides a single implementation that can be reused by any entrypoint.
"""

import csv
import logging
import os
import subprocess
from ftplib import FTP, all_errors

import xlrd
import xlrd.biffh
from decouple import config
from colorama import Fore
from typing import Optional

logger = logging.getLogger(__name__)

FTP_TIMEOUT = None


def csv_from_excel(
    xls_file: Optional[str] = None, csv_file: Optional[str] = None
) -> None:
    """Read *xls_file* and write its contents to *csv_file*.

    Parameters
    ----------
    xls_file: str, optional
        Source Excel file name. Defaults to ``Data_EO.xls``.
    csv_file: str, optional
        Destination CSV file name. Defaults to ``Data_EO.csv``.
    """

    xls_file = xls_file or config("XLS_FILE", default="Data_EO.xls")
    csv_file = csv_file or config("CSV_FILE", default="Data_EO.csv")

    counter = 0
    try:
        workbook = xlrd.open_workbook(xls_file)
        sheet = workbook.sheet_by_index(0)
    except FileNotFoundError as exc:
        logger.error(
            Fore.RED
            + f"Opening the {xls_file} file failed, please make sure that the file exists in the folder."
        )
        raise
    except xlrd.biffh.XLRDError as exc:
        logger.error(
            Fore.RED
            + f"Failed to open {xls_file}: {exc}. The file may be corrupt or in an unsupported format."
        )
        raise

    try:
        with open(csv_file, "w", newline="") as csv_handle:
            writer = csv.writer(csv_handle, quoting=csv.QUOTE_NONNUMERIC)
            for row in range(sheet.nrows):
                writer.writerow(sheet.row_values(row))
                counter += 1
                logger.info(f"{sheet.row_values(row)}")
    except (OSError, IOError) as exc:
        logger.error(
            Fore.RED + f"Failed to write to CSV file {csv_file}: {exc}"
        )
        raise

    logger.info(Fore.GREEN + f"Total records in the csv file ------> {counter}")


def ftp_upload(file_transfer_name: Optional[str] = None) -> None:
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

        file_transfer_name = file_transfer_name or config("CSV_FILE", default="Data_EO.csv")

        # Transfer CSV file to the IBM i IFS folder
        csv_name = os.path.basename(file_transfer_name)
        with open(file_transfer_name, "rb") as csv_file:
            ftp.storlines(f"STOR {csv_name}", csv_file)
            logger.info(f"Transferred {file_transfer_name}")

        ftp.quit()

        # Call the interface to connect to IBM i via FTP and invoke update programs
        subprocess.run(["ftp_cl_as400.bat"], check=True)

        # Successfully completed process
        subprocess.run(["python", "payroll_process_done.py"], check=True)

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

