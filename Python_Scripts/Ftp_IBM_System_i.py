#*************************************************************************************
# Purpose:  This Script  is designed to illustrate how to use a  connection on IBM
# System i  FTP Server, using the connect and login methods with Python.     
#                                                                                               
#*************************************************************************************
#  -*- coding: utf-8 -*-
from ftplib import FTP, error_perm, all_errors
from decouple import config, UndefinedValueError

FTP_TIMEOUT = None

ftp = FTP()
try:
    user = config('user')
    password = config('password')
    try:
        ftp.connect(config('Host', default='PUB400.COM'), 21, timeout=FTP_TIMEOUT)
    except (OSError, all_errors) as exc:
        print('FTP connection failed:', exc)
    else:
        try:
            ftp.login(user, password)
            print('Welcome to  =>', ftp.getwelcome())
        except error_perm as exc:
            print('FTP login failed:', exc)
except UndefinedValueError as exc:
    print('Missing credentials:', exc)
finally:
    ftp.close()
