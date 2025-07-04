#!/bin/bash

# Must be run as root or using sudo
if [[ $EUID -ne 0 && -z "$SUDO_USER" ]]; then
    echo "[Error] Please run this script with sudo or as root."
    exit 1
fi

echo "[...] Detecting OS..."

OS=""
PKG_MANAGER=""

# ---------------------
# Detect OS
# ---------------------
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
else
    echo "[✘] Unsupported OS: $OSTYPE"
    exit 1
fi

echo "[Success] Detected OS: $OS"

# ---------------------
# Determine Package Manager
# ---------------------
case "$OS" in
    ubuntu|debian)
        PKG_MANAGER="apt"
        ;;
    fedora)
        PKG_MANAGER="dnf"
        ;;
    centos|rhel)
        PKG_MANAGER="yum"
        ;;
    arch)
        PKG_MANAGER="pacman"
        ;;
    opensuse*)
        PKG_MANAGER="zypper"
        ;;
    alpine)
        PKG_MANAGER="apk"
        ;;
    macos)
        PKG_MANAGER="brew"
        ;;
    windows)
        PKG_MANAGER="choco"
        ;;
    *)
        echo "[Error] Unknown Linux distribution: $OS"
        exit 1
        ;;
esac

# ---------------------
# Verify Tool Availability
# ---------------------
if ! command -v "$PKG_MANAGER" &> /dev/null; then
    echo "[Error] Package manager '$PKG_MANAGER' not found on this system."
    echo "    -> Please install or repair your package manager manually."
    exit 1
fi

# ---------------------
# Run Update Commands
# ---------------------
echo "🔄 Starting system update with $PKG_MANAGER..."

case "$PKG_MANAGER" in
    apt)
        sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y
        ;;
    dnf)
        sudo dnf upgrade --refresh -y
        ;;
    yum)
        sudo yum update -y
        ;;
    pacman)
        sudo pacman -Syu --noconfirm
        ;;
    zypper)
        sudo zypper refresh && sudo zypper update -y
        ;;
    apk)
        sudo apk update && sudo apk upgrade
        ;;
    brew)
        sudo brew update && sudo brew upgrade
        ;;
    choco)
        sudo choco upgrade all -y
        ;;
esac

if [[ $? -eq 0 ]]; then
    echo "[Success] System updated successfully."
else
    echo "[Error] System update failed. Check logs and package manager health."
fi
