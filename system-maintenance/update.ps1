# update.ps1
# Cross-platform system updater script using PowerShell
# Windows (Chocolatey), macOS (Homebrew), Linux (apt, yum, dnf, etc.)

# Run this script as Administrator on Windows or with sudo on Linux/macOS.
#       Set-ExecutionPolicy Bypass -Scope Process -Force
#       .\update.ps1


# ----------------------------------------
# Check for Administrator Privileges
# ----------------------------------------
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(`
    [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[Error] Please run this script as Administrator." -ForegroundColor Red
    exit 1
}

Write-Host "[...] Detecting OS..." -ForegroundColor Yellow

# ----------------------------------------
# Detect OS
# ----------------------------------------
$OS = $null
$PackageManager = $null

if ($IsWindows) {
    $OS = "windows"
    $PackageManager = "choco"
} elseif ($IsMacOS) {
    $OS = "macos"
    $PackageManager = "brew"
} elseif ($IsLinux) {
    $OS = "linux"
    # Try to detect package manager
    if (Get-Command apt -ErrorAction SilentlyContinue) {
        $PackageManager = "apt"
    } elseif (Get-Command dnf -ErrorAction SilentlyContinue) {
        $PackageManager = "dnf"
    } elseif (Get-Command yum -ErrorAction SilentlyContinue) {
        $PackageManager = "yum"
    } elseif (Get-Command pacman -ErrorAction SilentlyContinue) {
        $PackageManager = "pacman"
    } elseif (Get-Command zypper -ErrorAction SilentlyContinue) {
        $PackageManager = "zypper"
    } elseif (Get-Command apk -ErrorAction SilentlyContinue) {
        $PackageManager = "apk"
    }
} else {
    Write-Host "[Error] Unsupported OS." -ForegroundColor Red
    exit 1
}

Write-Host "[Success] Detected OS: $OS" -ForegroundColor Green
Write-Host "[Success] Using Package Manager: $PackageManager" -ForegroundColor Green

# ----------------------------------------
# Verify Package Manager Exists
# ----------------------------------------
if (-not (Get-Command $PackageManager -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] Package manager '$PackageManager' not found." -ForegroundColor Red
    Write-Host "    -> Please install or repair it manually."
    exit 1
}

# ----------------------------------------
# Run Update Commands
# ----------------------------------------
Write-Host "Starting system update with $PackageManager..." -ForegroundColor Cyan

switch ($PackageManager) {
    "apt" {
        sudo apt update; sudo apt upgrade -y; sudo apt autoremove -y
    }
    "dnf" {
        sudo dnf upgrade --refresh -y
    }
    "yum" {
        sudo yum update -y
    }
    "pacman" {
        sudo pacman -Syu --noconfirm
    }
    "zypper" {
        sudo zypper refresh; sudo zypper update -y
    }
    "apk" {
        sudo apk update; sudo apk upgrade
    }
    "brew" {
        brew update; brew upgrade
    }
    "choco" {
        choco upgrade all -y
    }
    default {
        Write-Host "[Error] Unsupported package manager: $PackageManager" -ForegroundColor Red
        exit 1
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "[Success] System updated successfully." -ForegroundColor Green
} else {
    Write-Host "[Error] System update failed. Check logs and health." -ForegroundColor Red
}
