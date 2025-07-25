# ⚙️ System Engineer Automation Scripts

This repository is a collection of automation and system tools organized by **function**, not programming language. These scripts are designed to streamline operations, enhance security, and simplify systems management for Linux, MacOS and Windows environments and cloud platforms.

Each tool is built using **Python**, **Bash**, **Powershell**, **Go**, **Rust**, depending on performance, clarity, and system access needs.

<img src="https://github.com/HenokEshetu/System-Engineer-Automation-tools/blob/master/project-2.png?raw=true" width="100%" alt="" />

---

## 📁 Project Structure by Function

```
automation-scripts/
├── monitoring/
│ ├── cpu_memory_monitor.py
│ ├── disk_usage.go
│ ├── log_tailer.rs
│ ├── port_scanner.py
│
├── user-management/
│ ├── create_user.py
| ├── delete_user.py
| ├── list_user.py
| ├── lock_user.py
| ├── password_reset.py
| ├── bulk_create_users.py
│
├── system-maintenance/
│ ├── update.sh
│ ├── log_rotator.sh
│ ├── update.ps1
│ ├── log_rotator.ps1
│
├── security-auditing/
│ ├── find_suid.sh
│ ├── find_suid.ps1
│ ├── password_strength.py
│ ├── file_hasher.rs
│
├── deployment/
│ ├── deploy_docker.sh
│ ├── net_checker.go
│
├── backup/
│ ├── ec2_backup.py
│ ├── simple_backup.py
│ ├── rsync_backup.py
│ ├── mysql_backup.py
│ ├── encrypted_backup.py
│
└── README.md
```


---

## 🔍 Categories & Tools

### 🖥️ Monitoring Tools
| Script | Language | Description |
|--------|----------|-------------|
| `cpu_memory_monitor.py` | Python | Logs CPU and RAM usage every 5 seconds |
| `disk_usage.go` | Go | Reports CPU usage (total and per-core), Memory utilization (physical RAM), Disk usage (specified partition), Disk I/O rates (read/write operations), Network traffic (bytes sent/received), and System load averagese |
| `log_tailer.rs` | Rust | Real-time log tailer like `tail -f` |
| `port_scanner.py` | Python | Logs ping success/failure for uptime checks |

---

### 👤 User Management
| Script | Language | Description |
|--------|----------|-------------|
| `create_user.py` | Python | Automates Linux, MacOS and Windows user creation and SSH setup |
| `delete_user.py` | Python | Automates Linux, MacOS and Windows user deletion
| `list_user.py` | Python | Automates Linux, MacOS and Windows listing users
| `lock_user.py` | Python | Automates Linux, MacOS and Windows user suspension
| `reset_password.py` | Python | Automates Linux, MacOS and Windows password reset
| `bulk_create_users.py` | Python | Automates Linux, MacOS and Windows bulk users creation

---

### 🧹 System Maintenance
| Script | Language | Description |
|--------|----------|-------------|
| `update.sh` | Bash | Automates system update, upgrade, and cleanup which supports major operating systems |
| `log_rotator.sh` | Bash | Rotates logs when size exceeds 10MB and keeps the last 5 log archives |
| `update.ps1` | Powershell | Same as before |
| `log_rotator.ps1` | Powershell | Same as before |

---

### 🔐 Security Auditing
| Script | Language | Description |
|--------|----------|-------------|
| `find_suid.sh` | Bash | Finds SUID binaries for privilege auditing |
| `find_suid.ps1` | Powershell | Same as before |
| `password_strength.py` | Python | Checks password complexity |
| `file_hasher.rs` | Rust | A blazing-fast, cross-platform **file hashing and verification tool** written in Rust. Supports recursive directory traversal, multi-algorithm hashing, multithreading, and checksum validation. |

---

### 🚀 Deployment Automation
| Script | Language | Description |
|--------|----------|-------------|
| `deploy_docker.sh` | Bash | Pulls, stops, and redeploys Docker containers |
| `net_checker.go` | Go | Checks network port availability (TCP ping) |

---

### ☁️ Backup & Recovery
| Script | Language | Description |
|--------|----------|-------------|
| `ec2_backup.py` | Python | Creates EC2 EBS volume snapshots using tags |
| `simple_backup.py` | Python | Compress Home Directory (with exclusions) |
| `rsync_backup.py` | Python | Rsync-like Backup using `filecmp` + `shutil` |
| `mysql_backup.py` | Python | MySQL Backup with Rotation |
| `encrypted_backup.py` | Python | Archive + Encrypt with GPG |

---

## 💻 Requirements

| Language | Tools/Libraries |
|------------|----------------------------------------|
| Python | `psutil`, `boto3`, `shutil`, `tarfile`, `subprocess` (standard library) |
| Go | `gopsutil`                             |
| Rust | `sha2`, `chrono` (optional)            |
| Bash | POSIX-compatible shell, coreutils      |
| Powershell | Windows PowerShell 5+ or PowerShell Core|

> `gpg` is required for encrypted backups.  
> AWS credentials must be configured for EC2 scripts (`~/.aws/credentials`).

---

## ✅ Usage Examples

```bash
# Run system update and cleanup
bash system-maintenance/update.sh

# Create user with SSH access
sudo python3 user-management/create_user.py

# Monitor system usage
python3 monitoring/cpu_memory_monitor.py

# Check and log reachable services
go run deployment/net_checker.go

# Compile and run Rust SHA256 file hasher
rustc security-auditing/file_hasher.rs && ./file_hasher

# Backup EC2 volumes tagged for backup
python3 backup/ec2_backup.py
```

## 📬 Contact

If you are interested in collaborating or have questions about any script:

**Henok Eshetu**  
💼 Cybersecurity Professional & System Engineering Enthusiast  
📧 henokeshetu2025@proton.me  
🔗 [LinkedIn: henok-eshetu-284bba2b3](https://www.linkedin.com/in/henok-eshetu-284bba2b3/)  
🐙 [Github: @HenokEshetu](https://github.com/HenokEshetu)

---

## ⭐ Contributions

Feel free to fork this repository or suggest improvements through pull requests or issues.
