# IBM i Payroll Upload Tool

Convert an Excel payroll extract to CSV, upload it to the IBM i (formerly AS/400) Integrated File System (IFS), then invoke a program to apply salary adjustments. Works over SSH/SFTP (default) or FTPS.

**Flow:** XLS → CSV → IFS upload → CALL LIB/PROGRAM (PARMS)

![GUI flow](docs/gui_flow.png)

## Requirements
- Python 3.10+
- OS packages: `python3-tk`, `openssh-client`, `make`
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Copy the example environment and fill in secrets:
  ```bash
  cp .env.example .env  # then edit
  ```

## Usage
```bash
payroll --dry-run  # validate file without uploading
payroll            # run GUI, confirm, upload & call
```

## Configuration
Credentials and connection details are read from environment variables or a `.env` file:

| Variable | Description |
|----------|-------------|
| `HOST` | IBM i host name |
| `USER` | User profile |
| `PASSWORD` | Password (or use `SSH_KEY`) |
| `REMOTE_DIR` | IFS directory such as `/home/payroll` |
| `LIB` | Library containing the program |
| `PROGRAM` | Program name |
| `USE_SSH` | `1` to use SSH/SFTP, `0` for FTPS |

Secrets should never be committed; store them in a local `.env` or a secrets manager.

## CSV schema
The payroll CSV must contain two columns:

| Column | Type | Example |
|--------|------|---------|
| `emp_id` | string | `1001` |
| `amount` | decimal | `1234.56` |

A sample file is provided in [`examples/payroll_sample.csv`](examples/payroll_sample.csv).

## IBM i specifics
- IFS paths use forward slashes, e.g. `/home/payroll/in.csv`
- QSYS.LIB objects follow `LIB/FILE(MEMBER)` syntax
- Programs can be invoked with:
  ```bash
  system "CALL LIB/PROGRAM PARM('ARG1' 'ARG2')"
  ```

## Security
- Uses SFTP or FTPS to transfer files; plain FTP is not supported
- Credentials are loaded from environment variables
- Rotate any credentials previously committed to history

## Repository
- Sample data lives in [`examples/`](examples/)
- See [CONTRIBUTING](CONTRIBUTING.md) for development guidelines
- Licensed under the [MIT License](LICENSE)

