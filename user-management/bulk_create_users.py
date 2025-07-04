import csv
from create_user import create_user_linux  # or import from the refactored module


def bulk_create(path):
    with open(path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            username = row[0]
            print(f"Creating user: {username}")
            create_user_linux(username)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 bulk_create_users.py bulk_users.csv")
        sys.exit(1)
    bulk_create(sys.argv[1])
