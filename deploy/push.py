"""Upload this repository to the server over SSH and run deploy/deploy.sh.

    SSH_HOST=31.130.130.195 SSH_USER=root SSH_PASSWORD=... DOMAIN=archacrm.twc1.net python deploy/push.py

Honours HTTPS_PROXY (HTTP CONNECT) when the SSH port is only reachable through a proxy.
Requires `pip install paramiko`.
"""
from __future__ import annotations

import io
import os
import socket
import subprocess
import sys
import tarfile
import urllib.parse

import paramiko

HOST = os.environ.get("SSH_HOST", "31.130.130.195")
USER = os.environ.get("SSH_USER", "root")
PASSWORD = os.environ.get("SSH_PASSWORD") or sys.exit("SSH_PASSWORD is required")
DOMAIN = os.environ.get("DOMAIN", "archacrm.twc1.net")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE_SRC = "/opt/tenders-src"


def open_socket() -> socket.socket:
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if not proxy:
        return socket.create_connection((HOST, 22), timeout=30)
    p = urllib.parse.urlparse(proxy)
    s = socket.create_connection((p.hostname, p.port), timeout=30)
    s.sendall(f"CONNECT {HOST}:22 HTTP/1.1\r\nHost: {HOST}:22\r\n\r\n".encode())
    reply = b""
    while b"\r\n\r\n" not in reply:
        chunk = s.recv(1)
        if not chunk:
            raise RuntimeError("proxy closed the connection")
        reply += chunk
    status = reply.split(b"\r\n")[0].decode(errors="replace")
    if " 200 " not in status:
        raise RuntimeError("proxy refused CONNECT: " + status)
    return s


def bundle() -> bytes:
    files = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).split()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for f in files:
            tar.add(os.path.join(ROOT, f), arcname=f)
    return buf.getvalue()


def run(ssh: paramiko.SSHClient, cmd: str) -> int:
    print(f"$ {cmd}")
    _, out, err = ssh.exec_command(cmd, get_pty=True)
    for line in iter(out.readline, ""):
        print(line, end="")
    code = out.channel.recv_exit_status()
    if code:
        print(err.read().decode(), file=sys.stderr)
    return code


def main() -> int:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, sock=open_socket(), timeout=30, banner_timeout=30, look_for_keys=False, allow_agent=False)
    print("connected to", HOST)
    data = bundle()
    with ssh.open_sftp() as sftp:
        sftp.putfo(io.BytesIO(data), "/tmp/tenders.tgz")
    print(f"uploaded {len(data) // 1024} KB")
    cmds = [
        f"rm -rf {REMOTE_SRC} && mkdir -p {REMOTE_SRC} && tar -xzf /tmp/tenders.tgz -C {REMOTE_SRC}",
        f"DOMAIN={DOMAIN} SRC_DIR={REMOTE_SRC} bash {REMOTE_SRC}/deploy/deploy.sh",
    ]
    for c in cmds:
        if run(ssh, c):
            return 1
    ssh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
