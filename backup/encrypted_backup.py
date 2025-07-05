import os
import tarfile
import subprocess
from datetime import datetime

SRC = os.path.expanduser("~/projects")
DEST = "/mnt/backup_drive/encrypted"
EMAIL = "your@email.com"

timestamp = datetime.now().strftime("%Y-%m-%d")
archive = f"projects_{timestamp}.tar.gz"
archive_path = os.path.join(DEST, archive)
encrypted_path = archive_path + ".gpg"

os.makedirs(DEST, exist_ok=True)

with tarfile.open(archive_path, "w:gz") as tar:
    tar.add(SRC, arcname=os.path.basename(SRC))

subprocess.call(
    ["gpg", "--output", encrypted_path, "--encrypt", "--recipient", EMAIL, archive_path]
)
os.remove(archive_path)

print(f"[Success] Encrypted backup created: {encrypted_path}")
