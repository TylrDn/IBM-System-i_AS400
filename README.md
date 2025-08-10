# IBM System i / AS400 Payroll Interface

This repository contains scripts and examples for transferring payroll data from a local system Excel spreadsheet to an IBM i (AS/400) server. The main workflow converts an `.xls` template to CSV, uploads it to the IBM i integrated file system and triggers server-side programs to apply salary adjustments. Sample Python and Java snippets for connecting to IBM i are also included.

## Directory layout
- `payroll.py` – Tkinter GUI entrypoint. Displays a confirmation window and, on approval, runs `payroll_b.py`.
- `payroll_b.py` – Reads `Data_EO.xls`, writes `Data_EO.csv`, uploads via FTP to the IBM i and invokes `ftp_cl_as400.bat`.
- `ftp_cl_as400.bat` – Windows batch script that logs into the IBM i using credentials from `.env` and calls the server program `Temporal/Uti933_C`.
- `Data_EO.xls` – Example payroll spreadsheet; converted to `Data_EO.csv` during processing.
- `Python_Scripts/` – Examples of connecting to IBM i using Python (`AS400_ODBC_Conecction.py`, `Ftp_IBM_System_i.py`).
- `Java_Scripts/` – Example JDBC connection to IBM i (`AS400JConecction.java`).
- `requirements.txt` – Python dependencies.
- `setup.py` – Build script for packaging `payroll.py` into a Windows executable with `py2exe`.
- `src/` – Copy of the project files for distribution.

## Requirements
- Python 3.8 or later.
- Access to an IBM i (AS/400) server.
- Dependencies installed with:
  ```bash
  pip install -r requirements.txt
  ```
- A `.env` file in the project directory containing:
  ```
  Host=your.ibm.server
  user=USER_PROFILE
  password=PASSWORD
  ```

### Using the public PUB400 IBM i server
If you do not have access to an IBM i, you can create a free account at
[pub400.com](https://pub400.com). After registering, copy `.env.example` to
`.env` and update the `user` and `password` values with your PUB400
credentials. The `Host` value should remain `PUB400.COM`.

## Usage
1. Place `Data_EO.xls` in the project directory. The script will generate `Data_EO.csv`.
2. Run the GUI:
   ```bash
   python payroll.py
   ```
3. Confirm the prompt. The application shows a progress bar and launches `payroll_b.py`, which:
   - Converts the Excel data to CSV.
   - Uploads the CSV to the IBM i via FTP.
   - Executes `ftp_cl_as400.bat` to run the server-side update program.
4. After the batch script finishes, the process terminates.

## Building a Windows executable
Use `py2exe` to create a standalone executable:
```bash
python setup.py py2exe
```
The generated `payroll.exe` will appear in the `dist` directory.

## Example scripts
The `Python_Scripts` and `Java_Scripts` folders contain short examples demonstrating FTP, ODBC and JDBC connections to an IBM i server. They serve as references for integrating other applications.

## License
This project is released under the MIT License.
