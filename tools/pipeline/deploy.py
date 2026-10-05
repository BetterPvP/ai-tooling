"""Deploys the current checkout to ClansTest-1.

Uploads every jar in build/ whose name already exists in the server's /plugins, restarts the server and waits until
it reports running. Run `./gradlew shadowJar` first. The panel key comes from `PTERODACTYL_API_KEY`, or else from
1Password, and is never printed.

    python .claude/pipeline/deploy.py
"""
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid

PANEL = "https://panel.betterpvp.net/api/client/servers/14affb56"
KEY_REF = "op://Claude/pterodactyl-betterpvp/credential"


def key():
    if os.environ.get("PTERODACTYL_API_KEY"):
        return os.environ["PTERODACTYL_API_KEY"]
    return subprocess.run(["op", "read", KEY_REF], capture_output=True, text=True, check=True).stdout.strip()


def call(token, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(PANEL + path, data=data, method=method, headers={
        "Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    return json.loads(raw) if raw else {}


def upload(token, jars):
    url = call(token, "GET", "/files/upload")["attributes"]["url"]
    boundary = uuid.uuid4().hex
    parts = []
    for jar in jars:
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"{jar.name}\"\r\n"
                     f"Content-Type: application/java-archive\r\n\r\n".encode() + jar.read_bytes() + b"\r\n")
    body = b"".join(parts) + f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{url}&directory={urllib.parse.quote('/plugins')}", data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    urllib.request.urlopen(req, timeout=600).read()


def main():
    build = pathlib.Path.cwd() / "build"
    token = key()
    listing = call(token, "GET", "/files/list?directory=%2Fplugins")["data"]
    installed = {f["attributes"]["name"] for f in listing}
    jars = sorted(j for j in build.glob("*.jar") if j.name in installed)
    if not jars:
        sys.exit(f"No jars in {build} match the server's plugins. Run ./gradlew shadowJar first.")
    print("Uploading", ", ".join(j.name for j in jars))
    upload(token, jars)
    call(token, "POST", "/power", {"signal": "restart"})
    print("Restarting ClansTest-1")
    time.sleep(15)
    for _ in range(84):
        state = call(token, "GET", "/resources")["attributes"]["current_state"]
        if state == "running":
            print("ClansTest-1 is running")
            return
        time.sleep(5)
    sys.exit("ClansTest-1 did not report running within 7 minutes. Check the panel console.")


if __name__ == "__main__":
    main()
