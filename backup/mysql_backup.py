import os
import subprocess
from datetime import datetime

DB_USER = "root"
DB_PASS = "your_password"
DB_NAME = "mydatabase"
BACKUP_DIR = "/mnt/backup_drive/mysql"
ROTATE_KEEP = 5

os.makedirs(BACKUP_DIR, exist_ok=True)


def rotate_backups():
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".sql.gz")])
    while len(backups) > ROTATE_KEEP:
        os.remove(os.path.join(BACKUP_DIR, backups.pop(0)))


def backup_mysql():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"db_{DB_NAME}_{timestamp}.sql.gz"
    filepath = os.path.join(BACKUP_DIR, filename)
    cmd = f"mysqldump -u{DB_USER} -p{DB_PASS} {DB_NAME} | gzip > {filepath}"
    result = subprocess.call(cmd, shell=True)
    if result == 0:
        rotate_backups()
        print(f"[Success] MySQL backup saved to {filepath}")
    else:
        print("[Error] Backup failed.")


backup_mysql()
