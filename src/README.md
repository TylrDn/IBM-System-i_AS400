# IBM i (AS/400) Python Interface

## Features
- Easy installation
- Processes large data sets
- Compatible with Windows 10 or later, Python 3.8+, and IBM i OS 6.0+
- Only users with the installed executable can access the system

## Installation
- Place the `.xls` and `.csv` templates in the `Python_Payroll` folder and in the IBM i IFS (Integrated File System).
- Language and auxiliary libraries: Python 3.8 and Windows batch files.
- Database tools: IBM DB2/400.
- On the client machine ensure:
  - Microsoft Windows 10 or later
  - The `Python_Nomina` folder containing all required files (`.xls`, `.bat`, `.dll`, `.csv`)
  - A VPN connection to the IBM i server

## Usage
The `PAYROLL` executable reads an `.xls` file containing employee salaries, converts it to `.csv`, and updates the IBM i server database automatically.

## License
This project is licensed under the MIT License.

## Contact
- Name: Clay Lancini
- Email: claylanzino@gmail.com
- GitHub: [ClayLanzino](https://github.com/ClayLanzino)

