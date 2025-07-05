import os
import tarfile
from datetime import datetime

SRC_DIR = os.path.expanduser("~")
DEST_DIR = "/mnt/backup_drive/home_backup"
EXCLUDES = {"Downloads", ".cache"}
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
BACKUP_NAME = f"home_backup_{TIMESTAMP}.tar.gz"
LOG_FILE = "/var/log/simple_backup.log"

os.makedirs(DEST_DIR, exist_ok=True)


def is_excluded(path):
    return any(exclude in path for exclude in EXCLUDES)


def backup():
    archive_path = os.path.join(DEST_DIR, BACKUP_NAME)
    with tarfile.open(archive_path, "w:gz") as tar:
        for root, dirs, files in os.walk(SRC_DIR):
            for name in files:
                full_path = os.path.join(root, name)
                if not is_excluded(full_path):
                    tar.add(full_path, arcname=os.path.relpath(full_path, SRC_DIR))
    return archive_path


try:
    result = backup()
    print(f"[Success] Backup created: {result}")
except Exception as e:
    print(f"[Error] Backup failed: {e}")
