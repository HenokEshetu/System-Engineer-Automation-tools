import platform
import subprocess
import sys


def lock_user(username):
    os_type = platform.system()
    try:
        if os_type == "Linux":
            subprocess.run(["sudo", "passwd", "-l", username], check=True)
        elif os_type == "Darwin":
            subprocess.run(
                ["sudo", "pwpolicy", "-u", username, "-setpolicy", "isDisabled=1"],
                check=True,
            )
        elif os_type == "Windows":
            subprocess.run(
                ["powershell", "-Command", f'Disable-LocalUser -Name "{username}"'],
                check=True,
            )
        else:
            print("Unsupported OS")
            return
        print(f"[Success] User '{username}' locked.")
    except subprocess.CalledProcessError:
        print(f"[Error] Failed to lock user '{username}'.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 lock_user.py <username>")
        sys.exit(1)
    lock_user(sys.argv[1])
