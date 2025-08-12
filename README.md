# IBM System i / AS400 Payroll Interface

This repository contains scripts for transferring payroll data from a local
Excel spreadsheet to an IBM i (AS/400) server. The main workflow converts an
`.xls` template to CSV, uploads it to the IBM i integrated file system and
triggers server-side programs to apply salary adjustments. Sample Python and
Java snippets for connecting to IBM i are also included.

## Directory layout
- `payroll.py` – Tkinter GUI entrypoint. Displays a confirmation window and,
  on approval, runs `payroll_b.py`.
- `payroll_b.py` – Reads `Data_EO.xls`, writes `Data_EO.csv`, uploads via FTP
  to the IBM i and invokes the target program over FTP RCMD or SSH.
- `ibmi_transfer.py` – Helpers for FTP uploads and remote program execution.
- `legacy/` – Archived Windows artifacts (`ftp_cl_as400.bat`, `payroll.exe`).
- `Python_Scripts/`, `Java_Scripts/` – Sample connections to IBM i.
- `requirements.txt` – Python runtime dependencies.
- `setup.py` / `pyinstaller.spec` – Packaging scripts.

## Requirements
- Python 3.8 or later.
- Access to an IBM i (AS/400) server reachable over FTP or SSH.
- Dependencies installed with:
  ```bash
  pip install -r requirements.txt
  ```
- A `.env` file in the project directory containing:
  ```ini
  HOST=your.ibm.server
  USER=USER_PROFILE
  PASSWORD=PASSWORD
  REMOTE_DIR=/path/on/ifs
  LIB=YOURLIB
  PROGRAM=YOURPROGRAM
  USE_SSH=0
  ```

### Linux setup
On Debian/Ubuntu systems install prerequisites and run the interface with:
```bash
sudo apt-get install python3-tk openssh-client make
make run
```
The GUI will convert `Data_EO.xls` to `Data_EO.csv`, upload it and invoke the
IBM i program specified in `.env`.

### Packaging
To build a distributable using PyInstaller:
```bash
make package
```
Set `PYI_ONEFILE=1` to create a single-file binary.

## License
This project is released under the MIT License.

## Staging ingest/apply workflow

An additional, SSH/SFTP-only pipeline stages a CSV/XLSX file on IBM i, runs
server-side validation and merges into shadow tables.

### Quickstart

```bash
make install
python -m src.runner --file tests/smoke_local.csv --dry-run
```

Remove `--dry-run` and populate `.env` with real host details to execute
against an IBM i partition.

### Configuration

`.env` keys:

```
IBMI_HOST=hostname
IBMI_USER=user
IBMI_SSH_KEY=/path/to/key
#IBMI_PASSWORD=optional
LIB_STG=MYLIB
IFS_STAGING_DIR=/home/user/staging
JOBQ=QSYSNOMAX
OUTQ=QPRINT
ALLOW_AUTO_HOSTKEY=false
```

### Troubleshooting

- Use `--dry-run` to preview actions without side effects.
- Ensure the user profile can create objects in `${LIB_STG}` and write to
  `${IFS_STAGING_DIR}`.
- All processing occurs in staging libraries and directories only.

### Why this won’t modify your existing codebase destructively

The workflow is additive: it creates objects only in the staging library
`${LIB_STG}` and directory `${IFS_STAGING_DIR}`. No production libraries,
queues or existing source files are touched.
