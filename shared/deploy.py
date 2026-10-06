"""Deploys the current checkout to ClansTest-1.

Uploads every jar in build/ whose name already exists in the server's /plugins, restarts the server and waits until
it reports running. Run `./gradlew shadowJar` first. The panel key comes from `PTERODACTYL_API_KEY`, or else from
1Password, and is never printed.

With --pack it also builds the resource pack, with the GUI screen art of this checkout, and unpacks it into Nexo's
pack folder, which Nexo serves after the restart. The Resourcepack repo is found next to the BetterPvP checkout, or
at `RESOURCEPACK_DIR`.

    python .claude/shared/deploy.py [--pack]
"""
import argparse
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
NEXO_PACK = "/plugins/Nexo/pack"
PACK_UPLOAD = "betterpvp-deploy.zip"


def key():
    if os.environ.get("PTERODACTYL_API_KEY"):
        return os.environ["PTERODACTYL_API_KEY"]
    return subprocess.run(["op", "read", KEY_REF], capture_output=True, text=True, check=True).stdout.strip()


def call(token, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(PANEL + path, data=data, method=method, headers={
        "Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read()
    return json.loads(raw) if raw else {}


def upload(token, files, directory="/plugins", names=None):
    url = call(token, "GET", "/files/upload")["attributes"]["url"]
    boundary = uuid.uuid4().hex
    parts = []
    for index, file in enumerate(files):
        name = names[index] if names else file.name
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"{name}\"\r\n"
                     f"Content-Type: application/octet-stream\r\n\r\n".encode() + file.read_bytes() + b"\r\n")
    body = b"".join(parts) + f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{url}&directory={urllib.parse.quote(directory)}", data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    urllib.request.urlopen(req, timeout=600).read()


def resourcepack():
    if os.environ.get("RESOURCEPACK_DIR"):
        return pathlib.Path(os.environ["RESOURCEPACK_DIR"])
    for parent in pathlib.Path.cwd().parents:
        if (parent / "Resourcepack" / "pack_processor.py").is_file():
            return parent / "Resourcepack"
    sys.exit("No Resourcepack repo next to this checkout. Set RESOURCEPACK_DIR.")


def deploy_pack(token):
    repo = resourcepack()
    subprocess.run([sys.executable, "pack_processor.py", "pack", "--betterpvp", str(pathlib.Path.cwd())],
                   cwd=repo, check=True)
    print("Unpacking the pack into", NEXO_PACK)
    upload(token, [repo / "pack.zip"], NEXO_PACK, [PACK_UPLOAD])
    call(token, "POST", "/files/decompress", {"root": NEXO_PACK, "file": PACK_UPLOAD})
    call(token, "POST", "/files/delete", {"root": NEXO_PACK, "files": [PACK_UPLOAD]})


def main():
    parser = argparse.ArgumentParser(description="Deploys this checkout to ClansTest-1.")
    parser.add_argument("--pack", action="store_true", help="Also build the resource pack and unpack it into Nexo.")
    args = parser.parse_args()
    build = pathlib.Path.cwd() / "build"
    token = key()
    listing = call(token, "GET", "/files/list?directory=%2Fplugins")["data"]
    installed = {f["attributes"]["name"] for f in listing}
    jars = sorted(j for j in build.glob("*.jar") if j.name in installed)
    if not jars and not args.pack:
        sys.exit(f"No jars in {build} match the server's plugins. Run ./gradlew shadowJar first.")
    if args.pack:
        deploy_pack(token)
    if jars:
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
