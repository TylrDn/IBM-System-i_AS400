# Project Setup Guide

This guide walks you through configuring the IBM i (formerly AS/400) payroll
interface for local development or demonstration.

## 1. Requirements
- **Python**: version 3.8 or later
- **IBM i access**: either your own server or a free PUB400 account
- **Linux prerequisites** (Debian/Ubuntu):
  ```bash
  sudo apt-get install python3-tk openssh-client make
  ```

## 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

## 3. Configure connection secrets
1. Duplicate `.env.example` and rename it to `.env`.
2. Replace each placeholder with real credentials:
   ```ini
   HOST=your.ibm.server   # e.g., PUB400.COM
   USER=YOUR_USER_ID      # IBM i user profile
   PASSWORD=YOUR_PASSWORD # IBM i password
   REMOTE_DIR=/path/on/ifs
   LIB=YOURLIB
   PROGRAM=YOURPROGRAM
   USE_SSH=0              # set to 1 to call program via SSH
   ```
   > **Never commit** your filled-in `.env` file to source control.

## 4. Prepare payroll data
- Use `examples/payroll_sample.csv` as a template for your own payroll data.

## 5. Run the interface
```bash
make run
```
Confirm the prompt. The script converts the Excel file, uploads it securely to the IBM i, and executes the remote program (via SSH or FTPS `RCMD`).

## 6. Packaging
To build a Linux distributable:
```bash
make package
```
Set `PYI_ONEFILE=1` to create a single-file binary.

You're now ready to demonstrate the payroll interface. Good luck!
