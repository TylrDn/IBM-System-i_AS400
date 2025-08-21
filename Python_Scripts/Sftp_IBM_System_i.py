"""Example secure SFTP connection to an IBM i server.

Credentials are read from environment variables ``USER`` and ``PASSWORD``.
The default host is ``PUB400.COM`` but can be overridden via ``HOST``.
"""

import os

import paramiko


def main() -> None:
    host = os.environ.get("HOST", "PUB400.COM")
    user = os.environ.get("USER")
    password = os.environ.get("PASSWORD")
    if not all([user, password]):
        raise RuntimeError("Missing USER or PASSWORD environment variables")

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    sftp = None
    try:
        client.connect(host, username=user, password=password)
        sftp = client.open_sftp()
        print("SFTP connection established to", host)
    finally:
        if sftp is not None:
            sftp.close()
        client.close()


if __name__ == "__main__":
    main()

