# Project Setup Guide

This guide walks you through configuring the IBM System i / AS400 Payroll Interface for local development or demonstration.

## 1. Requirements
- **Python**: version 3.8 or later.
- **IBM i (AS/400) access**: either your own server or a free PUB400 account.
- **Windows utilities**: the workflow calls a Windows batch file (`ftp_cl_as400.bat`), so run the project on Windows or adjust the script for another OS.

## 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

## 3. Configure connection secrets
1. Duplicate `.env.example` and rename it to `.env`.
2. Replace each placeholder with real credentials:
   ```ini
   Host=your.ibm.server   # e.g., PUB400.COM
   user=YOUR_USER_ID      # IBM i user profile
   password=YOUR_PASSWORD # IBM i password
   ```
   > **Never commit** your filled-in `.env` file to source control.

## 4. Prepare payroll data
- Place `Data_EO.xls` (or your own payroll spreadsheet with the same format) in the project root. The program converts it to `Data_EO.csv` automatically.

## 5. Run the interface
```bash
python payroll.py
```
Confirm the prompt. The script converts the Excel file, uploads it to the IBM i via FTP, and executes the remote program.

## 6. Optional: build a Windows executable
To package the GUI as `payroll.exe`:
```bash
pip install py2exe
python setup.py py2exe
```
The executable will appear in a new `dist/` directory.

## 7. Troubleshooting
- Ensure the IBM i server is reachable and your credentials are correct.
- Verify that `ftp_cl_as400.bat` has permission to run and that your system allows outbound FTP connections.

You are now ready to demonstrate the payroll interface during your IBM interview. Good luck!
