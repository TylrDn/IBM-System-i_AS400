"""Wrapper script for payroll utilities.

This script delegates its work to :mod:`payroll_utils` to avoid duplicating
implementation across multiple entry points.
"""

from payroll_utils import csv_from_excel, ftp_upload


if __name__ == "__main__":
    csv_from_excel()
    ftp_upload()

