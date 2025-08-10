#*************************************************************************************
# Purpose:  This Script  is designed to illustrate how to use a  connection on IBM
# System i  FTP Server, using the connect and login methods with Python.     
#                                                                                               
#*************************************************************************************
#  -*- coding: utf-8 -*-
from ftplib import FTP, error_perm
from decouple import config, UndefinedValueError

ftp = FTP()
try:
    user = config('user')
    password = config('password')
except UndefinedValueError as exc:
    print('Missing credentials:', exc)
else:
    ftp.connect(config('Host', default='PUB400.COM'), 21, -999)
    try:
        ftp.login(user, password)
        print('Welcome to  =>', ftp.getwelcome())
    except error_perm as exc:
        print('FTP login failed:', exc)
    finally:
        ftp.close()
