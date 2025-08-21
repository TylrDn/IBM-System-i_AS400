"""Utility functions for payroll data processing."""

import defusedcsv as csv
import logging
import os
from typing import Optional

import xlrd
import xlrd.biffh
from colorama import Fore

logger = logging.getLogger(__name__)


def _open_sheet(xls_file: str):
    """Return the first worksheet from *xls_file* with errors logged."""
    try:
        workbook = xlrd.open_workbook(xls_file)
        return workbook.sheet_by_index(0)
    except FileNotFoundError:
        logger.error(
            "%sOpening the %s file failed, please make sure that the file exists in the folder.",
            Fore.RED,
            xls_file,
        )
        raise
    except xlrd.biffh.XLRDError as exc:
        logger.error(
            "%sFailed to open %s: %s. The file may be corrupt or in an unsupported format.",
            Fore.RED,
            xls_file,
            exc,
        )
        raise


def _write_sheet_to_csv(sheet, csv_file: str) -> int:
    """Write *sheet* rows to *csv_file* and return the row count."""
    counter = 0
    try:
        with open(csv_file, "w", newline="") as csv_handle:
            writer = csv.writer(csv_handle, quoting=csv.QUOTE_NONNUMERIC)  # noqa: S603
            for row in range(sheet.nrows):
                writer.writerow(sheet.row_values(row))
                counter += 1
                logger.info("%s", sheet.row_values(row))
    except OSError as exc:
        logger.error(
            "%sFailed to write to CSV file %s: %s",
            Fore.RED,
            csv_file,
            exc,
        )
        raise
    return counter


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
    csv_file = csv_file or os.getenv("CSV_FILE", "examples/payroll_sample.csv")
    if xls_file is None or csv_file is None:
        raise ValueError("Missing path to XLS or CSV file")

    sheet = _open_sheet(xls_file)
    count = _write_sheet_to_csv(sheet, csv_file)
    logger.info("%sTotal records in the csv file ------> %s", Fore.GREEN, count)
