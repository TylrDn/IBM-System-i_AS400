#*************************************************************************************
# Purpose:  This Script  is designed to illustrate how to use a  connection on IBM
# System i  FTP Server, using the connect and login methods with Python.     
#                                                                                               
#*************************************************************************************
#  -*- coding: utf-8 -*-
from ftplib import FTP
from decouple import config

ftp = FTP()
ftp.connect(config('Host', default='PUB400.COM'), 21, -999)
ftp.login(config('user'), config('password'))
print('Welcome to  =>', ftp.getwelcome())
ftp.close()
