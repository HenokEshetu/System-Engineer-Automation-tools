import os
import platform
import subprocess
import sys


def delete_user(username):
    os_type = platform.system()
    try:
        if os_type == "Linux" or os_type == "Darwin":
            subprocess.run(["sudo", "userdel", "-r", username], check=True)
        elif os_type == "Windows":
            subprocess.run(
                ["powershell", "-Command", f'Remove-LocalUser -Name "{username}"'],
                check=True,
            )
        else:
            print("Unsupported OS")
            return
        print(f"[Success] User '{username}' deleted successfully.")
    except subprocess.CalledProcessError:
        print(f"[Error] Failed to delete user '{username}'.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 delete_user.py <username>")
        sys.exit(1)
    delete_user(sys.argv[1])
