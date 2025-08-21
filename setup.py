from setuptools import find_packages, setup

setup(
    name="ibmi-payroll",
    version="0.1.0",
    description="Excel payroll upload tool for IBM i (formerly AS/400)",
    author="Clay Lancini",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "Pillow>=10.3.0",
        "xlrd~=2.0.1",
        "colorama~=0.4.6",
        "python-dotenv~=1.0",
        "paramiko~=3.4",
        "pandas~=2.2",
    ],
    entry_points={
        "console_scripts": ["payroll=src.runner:main"],
    },
)
