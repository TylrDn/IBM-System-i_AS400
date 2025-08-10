"""Utility functions for payroll data processing and FTP upload.

This module consolidates logic previously duplicated across multiple scripts
and provides a single implementation that can be reused by any entrypoint.
"""

import csv
import logging
import os
import subprocess
import sys
from pathlib import Path
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
        Source Excel file name. Defaults to the ``XLS_FILE`` environment
        variable or ``Data_EO.xls`` if not set.
    csv_file: str, optional
        Destination CSV file name. Defaults to the ``CSV_FILE`` environment
        variable or ``Data_EO.csv`` if not set.
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
    """Upload the generated CSV to the IBM i server and run post-processing.

    Parameters
    ----------
    file_transfer_name: str, optional
        Path of the CSV to transfer. Defaults to the ``CSV_FILE`` environment
        variable or ``Data_EO.csv`` if not set.

    Raises
    ------
    ftplib.all_errors
        If any FTP error occurs.
    subprocess.CalledProcessError
        If any of the invoked subprocesses fail.
    FileNotFoundError
        If required script files are missing.
    """

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

        file_transfer_name = Path(
            file_transfer_name or config("CSV_FILE", default="Data_EO.csv")
        ).resolve()
        if not file_transfer_name.is_file():
            logger.error(Fore.RED + f"CSV file not found: {file_transfer_name}")
            raise FileNotFoundError(file_transfer_name)

        # Transfer CSV file to the IBM i IFS folder
        csv_name = file_transfer_name.name
        with file_transfer_name.open("rb") as csv_file:
            ftp.storlines(f"STOR {csv_name}", csv_file)
            logger.info(f"Transferred {file_transfer_name}")

        ftp.quit()

        # Call the interface to connect to IBM i via FTP and invoke update programs
        if os.name == "nt":
            bat_script = Path(__file__).with_name("ftp_cl_as400.bat")
            if not bat_script.is_file():
                logger.error(Fore.RED + f"Batch file not found: {bat_script}")
                raise FileNotFoundError(bat_script)
            subprocess.run(["cmd", "/c", str(bat_script)], check=True, shell=False)
        else:
            logger.info("Skipping Windows batch script on non-Windows platform")

        # Successfully completed process
        done_script = Path(__file__).resolve().with_name("payroll_process_done.py")
        if not done_script.is_file():
            logger.error(Fore.RED + f"Completion script not found: {done_script}")
            raise FileNotFoundError(done_script)
        subprocess.run([sys.executable, str(done_script)], check=True, shell=False)

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

