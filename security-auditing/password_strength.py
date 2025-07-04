import re


def check_strength(pw):
    if len(pw) < 8:
        return "Too short"
    if not re.search(r"[A-Z]", pw):
        return "No uppercase letter"
    if not re.search(r"\d", pw):
        return "No digit"
    if not re.search(r"\W", pw):
        return "No symbol"
    return "Strong password"


pw = input("Enter password to check: ")
print("Result:", check_strength(pw))
