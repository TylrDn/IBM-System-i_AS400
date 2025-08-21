# IBM i Payroll Upload Tool

Convert an Excel payroll extract to CSV, upload it to the IBM i (formerly AS/400) Integrated File System (IFS), and invoke a program to apply salary adjustments. The tool uses SSH/SFTP by default but also supports FTPS.

**Flow:** XLS → CSV → IFS upload → `CALL LIB/PROGRAM (PARMS)`

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

## CSV Schema
The payroll CSV must contain two columns:

| Column | Type | Example |
|--------|------|---------|
| `emp_id` | string | `1001` |
| `amount` | decimal | `1234.56` |

A sample file is provided in [`examples/payroll_sample.csv`](examples/payroll_sample.csv).

## IBM i Specifics
- IFS paths use forward slashes, for example `/home/payroll/in.csv`.
- QSYS.LIB objects follow the `LIB/FILE(MEMBER)` syntax.
- Programs can be invoked with:
  ```bash
  system "CALL LIB/PROGRAM PARM('ARG1' 'ARG2')"
  ```

## Security
- Uses SFTP or FTPS to transfer files; plain FTP is not supported.
- Credentials are loaded from environment variables.
- Rotate any credentials previously committed to history.

## Repository
- Sample data lives in [`examples/`](examples/).
- See [CONTRIBUTING](CONTRIBUTING.md) for development guidelines.
- Licensed under the [MIT License](LICENSE).


## PUB400 Quick Start
This project can connect to any IBM i, including PUB400, via SFTP/SSH or FTPS. Configure the application using variables defined in `.env`.

1. **Clone and set up**
   ```bash
   git clone https://github.com/TylrDn/IBM-System-i_AS400.git
   cd IBM-System-i_AS400
   bash scripts/setup_local.sh
   chmod +x scripts/*.sh
   ```

2. **Configure `.env`**

   Edit `.env` and replace placeholders:
   - `HOST=pub400` (or `pub400.com`)
   - `USER=your_pub400_username`
   - Use either `PASSWORD` or `SSH_KEY` (recommended) and leave the other blank.
   - Set `REMOTE_DIR` to a writable IFS path, e.g. `/home/<user>/incoming`
   - Set `LIB/PROGRAM` to the IBM i objects you will call
   - `USE_SSH=1` for SFTP/SSH

   Tip for non-standard ports: add an SSH alias so the app can use `HOST=pub400`:

   ```
   Host pub400
     HostName pub400.com
     Port 22
     User your_pub400_username
     IdentityFile ~/.ssh/id_ed25519
     StrictHostKeyChecking accept-new
     UserKnownHostsFile ~/.ssh/known_hosts
   ```

3. **Smoke test**

   ```bash
   bash scripts/smoke_test.sh
   ```

4. **Run**

   ```bash
   payroll --dry-run examples/payroll_mock.csv
   payroll
   ```

### Windows (PowerShell)

```powershell
git clone https://github.com/TylrDn/IBM-System-i_AS400.git
cd IBM-System-i_AS400
py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Create .env from template and fill placeholders
payroll --dry-run .\examples\payroll_mock.csv
payroll
```

Security notes
- Prefer SSH keys; keep `PASSWORD` empty if using `SSH_KEY`.
- First-time host key pinning: `ssh -o StrictHostKeyChecking=accept-new pub400`
- Restrict permissions: `chmod 600 .env ~/.ssh/id_*`

---
## After creation
- Ensure both scripts are executable:
  ```bash
  chmod +x scripts/*.sh
  ```
- Do not commit real secrets. Keep `.env` out of version control.
