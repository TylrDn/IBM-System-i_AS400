"""Utility functions for payroll data processing."""

import csv
import logging
import os
from typing import Optional

import xlrd
import xlrd.biffh
from colorama import Fore

logger = logging.getLogger(__name__)


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

    xls_file = xls_file or os.getenv("XLS_FILE", "examples/payroll_sample.xlsx")
    if xls_file is None:
        raise ValueError("Missing path to XLS file")
    csv_file = csv_file or os.getenv("CSV_FILE", "examples/payroll_sample.csv")
    if csv_file is None:
        raise ValueError("Missing path to CSV file")

    counter = 0
    try:
        workbook = xlrd.open_workbook(xls_file)
        sheet = workbook.sheet_by_index(0)
    except FileNotFoundError:
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
    except OSError as exc:
        logger.error(Fore.RED + f"Failed to write to CSV file {csv_file}: {exc}")
        raise

    logger.info(Fore.GREEN + f"Total records in the csv file ------> {counter}")
