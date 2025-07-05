import os
import shutil
import filecmp

SRC = os.path.expanduser("~/Documents")
DEST = "/mnt/backup_drive/incremental_docs"
EXCLUDE = {"node_modules", ".cache", "*.log"}

os.makedirs(DEST, exist_ok=True)


def should_exclude(name):
    return any(p in name for p in EXCLUDE)


def sync(src, dst):
    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        dst_root = os.path.join(dst, rel_root)

        for d in dirs:
            if not should_exclude(d):
                os.makedirs(os.path.join(dst_root, d), exist_ok=True)

        for f in files:
            if should_exclude(f):
                continue
            src_file = os.path.join(root, f)
            dst_file = os.path.join(dst_root, f)
            if not os.path.exists(dst_file) or not filecmp.cmp(
                src_file, dst_file, shallow=False
            ):
                shutil.copy2(src_file, dst_file)


sync(SRC, DEST)
print("[Success] Incremental backup completed.")
