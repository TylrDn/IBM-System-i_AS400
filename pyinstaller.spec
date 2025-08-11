# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None
onefile = bool(int(os.environ.get("PYI_ONEFILE", "0")))

a = Analysis(
    ['payroll.py'],
    pathex=[],
    binaries=[],
    datas=[('icons8-payroll-64.png', '.')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='payroll', console=True)
if onefile:
    coll = EXE(pyz, a.scripts, [], exclude_binaries=True, name='payroll', console=True)
else:
    coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, name='payroll')
