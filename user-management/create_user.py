import os
import subprocess

def create_user(username):
    subprocess.run(["sudo", "adduser", "--disabled-password", "--gecos", "", username])
    subprocess.run(["sudo", "mkdir", f"/home/{username}/.ssh"])
    subprocess.run(["sudo", "chmod", "700", f"/home/{username}/.ssh"])
    subprocess.run(["sudo", "cp", "~/.ssh/authorized_keys", f"/home/{username}/.ssh/"])
    subprocess.run(["sudo", "chown", "-R", f"{username}:{username}", f"/home/{username}/.ssh"])

if __name__ == "__main__":
    user = input("Enter the username to create: ")
    create_user(user)
    print(f"User '{user}' created with SSH access.")
