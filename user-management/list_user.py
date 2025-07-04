import platform
import subprocess


def list_users():
    os_type = platform.system()
    if os_type == "Linux" or os_type == "Darwin":
        with open("/etc/passwd") as f:
            for line in f:
                parts = line.split(":")
                if int(parts[2]) >= 1000 and parts[0] != "nobody":
                    print(parts[0])
    elif os_type == "Windows":
        subprocess.run(["powershell", "-Command", "Get-LocalUser | Select Name"])
    else:
        print("Unsupported OS")


if __name__ == "__main__":
    list_users()
