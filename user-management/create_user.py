"""
Notes for Windows
-----------------
- Requires PowerShell 5+
- Script must be run with Administrator privileges
- OpenSSH is not installed by default — user must enable manually via:
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
    Start-Service sshd
    Set-Service -Name sshd -StartupType 'Automatic'
"""

import subprocess
import platform
import os
import shutil
import sys


def detect_os():
    os_name = platform.system()
    if os_name == "Linux":
        return "linux"
    elif os_name == "Darwin":
        return "macos"
    elif os_name == "Windows":
        return "windows"
    else:
        return "unsupported"


def create_user_linux(username):
    try:
        subprocess.run(
            ["sudo", "useradd", "-m", "-s", "/bin/bash", username], check=True
        )
        print(f"[Success] User '{username}' created successfully on Linux.")
    except subprocess.CalledProcessError:
        print(f"[Error] Failed to create user '{username}' on Linux. It may already exist.")


def create_user_macos(username):
    try:
        subprocess.run(
            ["sudo", "dscl", ".", "-create", f"/Users/{username}"], check=True
        )
        subprocess.run(
            [
                "sudo",
                "dscl",
                ".",
                "-create",
                f"/Users/{username}",
                "UserShell",
                "/bin/bash",
            ],
            check=True,
        )
        subprocess.run(
            ["sudo", "dscl", ".", "-create", f"/Users/{username}", "UniqueID", "505"],
            check=True,
        )  # ensure unique UID
        subprocess.run(
            [
                "sudo",
                "dscl",
                ".",
                "-create",
                f"/Users/{username}",
                "PrimaryGroupID",
                "20",
            ],
            check=True,
        )
        subprocess.run(
            [
                "sudo",
                "dscl",
                ".",
                "-create",
                f"/Users/{username}",
                "NFSHomeDirectory",
                f"/Users/{username}",
            ],
            check=True,
        )
        subprocess.run(["sudo", "mkdir", f"/Users/{username}"], check=True)
        print(f"[Success] User '{username}' created successfully on macOS.")
    except subprocess.CalledProcessError as e:
        print(f"[Error] macOS user creation failed: {e}")


def create_user_windows(username):
    try:
        command = [
            "powershell",
            "-Command",
            f'New-LocalUser -Name "{username}" -NoPassword -AccountNeverExpires',
        ]
        subprocess.run(command, check=True)
        subprocess.run(
            [
                "powershell",
                "-Command",
                f"Add-LocalGroupMember -Group 'Users' -Member \"{username}\"",
            ],
            check=True,
        )
        print(f"[Success] User '{username}' created successfully on Windows.")
    except subprocess.CalledProcessError as e:
        print(f"[Error] Failed to create user '{username}' on Windows: {e}")


def setup_ssh_unix(username):
    try:
        user_home = (
            f"/home/{username}"
            if os.path.exists(f"/home/{username}")
            else f"/Users/{username}"
        )
        ssh_dir = os.path.join(user_home, ".ssh")
        auth_keys = os.path.join(ssh_dir, "authorized_keys")

        os.makedirs(ssh_dir, mode=0o700, exist_ok=True)
        shutil.copy(os.path.expanduser("~/.ssh/authorized_keys"), auth_keys)
        os.chmod(auth_keys, 0o600)

        import pwd

        uid = pwd.getpwnam(username).pw_uid
        gid = pwd.getpwnam(username).pw_gid
        os.chown(ssh_dir, uid, gid)
        os.chown(auth_keys, uid, gid)

        print(f"[Success] SSH keys set up for '{username}'.")
    except Exception as e:
        print(f"[Error] SSH setup failed: {e}")


def setup_ssh_windows(username):
    print(
        "[i] SSH setup for Windows is not automated. Ensure OpenSSH is installed and configured."
    )
    # Optionally check:
    result = subprocess.run(
        [
            "powershell",
            "-Command",
            "Get-WindowsCapability -Online | ? Name -like 'OpenSSH*'",
        ],
        capture_output=True,
    )
    print(result.stdout.decode())


if __name__ == "__main__":
    username = input("Enter the username to create: ").strip()
    os_type = detect_os()

    if not username:
        print("[Error] Username cannot be empty.")
        sys.exit(1)

    print(f"[i] Detected OS: {os_type}")

    if os_type == "linux":
        create_user_linux(username)
        setup_ssh_unix(username)
    elif os_type == "macos":
        create_user_macos(username)
        setup_ssh_unix(username)
    elif os_type == "windows":
        create_user_windows(username)
        setup_ssh_windows(username)
    else:
        print("[Error] Unsupported operating system.")
