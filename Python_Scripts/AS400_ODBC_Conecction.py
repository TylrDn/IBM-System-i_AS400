#**************************************************************************************#
# Purpose:  This Script  is designed to illustrate how to use a  connection to an IBM  #
# System i  Server, by using the connect and login methods.                            #
#  In addition a database file is connected using a connection (ODBC).                 #                                      #
#**************************************************************************************#
import os

import pyodbc


def main() -> None:
    system = os.environ.get("IBMI_SYSTEM")
    uid = os.environ.get("IBMI_UID")
    pwd = os.environ.get("IBMI_PWD")
    if not all([system, uid, pwd]):
        raise RuntimeError("Missing database connection environment variables")

    connection = pyodbc.connect(
        driver="{iSeries Access ODBC Driver}", system=system, uid=uid, pwd=pwd
    )
    c1 = connection.cursor()
    query = (
        "select employee_type, employee_code, employee_name, monthly_salary "
        "from dblibrary.nmpp000 where employee_type = ?"
    )
    for row in c1.execute(query, "O"):
        print(row)


if __name__ == "__main__":
    main()
