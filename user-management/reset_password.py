import getpass
import platform
import subprocess


def reset_password(username):
    password = getpass.getpass(prompt="Enter new password: ")

    os_type = platform.system()
    try:
        if os_type == "Linux" or os_type == "Darwin":
            subprocess.run(
                ["sudo", "chpasswd"],
                input=f"{username}:{password}".encode(),
                check=True,
            )
        elif os_type == "Windows":
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f'Set-LocalUser -Name "{username}" -Password (ConvertTo-SecureString "{password}" -AsPlainText -Force)',
                ],
                check=True,
            )
        print(f"[Success] Password for '{username}' reset.")
    except subprocess.CalledProcessError as e:
        print(f"[Error] Failed to reset password: {e}")


if __name__ == "__main__":
    user = input("Enter the username: ")
    reset_password(user)
