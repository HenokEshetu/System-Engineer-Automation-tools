import re


def check_strength(password):
    reasons = []

    if len(password) < 8:
        reasons.append("Too short (minimum 8 characters)")

    if not re.search(r"[A-Z]", password):
        reasons.append("Missing uppercase letter")

    if not re.search(r"[a-z]", password):
        reasons.append("Missing lowercase letter")

    if not re.search(r"\d", password):
        reasons.append("Missing digit")

    if not re.search(r"\W", password):
        reasons.append("Missing special character")

    if not reasons:
        return "Strong password"
    else:
        return "\n".join(reasons)


def main():
    try:
        pw = input("Enter password to check: ")
        result = check_strength(pw)
        print("\nResult:\n" + result)
    except KeyboardInterrupt:
        print("\n[!] Exited by user.")


if __name__ == "__main__":
    main()
