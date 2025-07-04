# 🔧 System Engineer Automation Scripts

Welcome to my automation scripts — a curated collection of real-world, production-ready scripts used to streamline system engineering tasks including maintenance, user management, container deployment, and cloud backups.

These scripts are written in **Bash** and **Python**, and showcase my ability to automate infrastructure, improve security, and increase operational efficiency as a **System Engineer with cybersecurity awareness**.

---

## 📁 Project Structure

automation-scripts/
│
├── 1-system-maintenance/
│ ├── update.sh
│ └── README.md
│
├── 2-user-management/
│ ├── create_user.py
│ └── README.md
│
├── 3-docker-deployment/
│ ├── deploy_docker.sh
│ └── README.md
│
├── 4-aws-ec2-backup/
│ ├── ec2_backup.py
│ └── README.md
│
└── README.md


---

## 🔐 Scripts Overview

### 1. 🧹 **System Maintenance Script** (Bash)
Automates package updates, cleanup, and logs the results for auditing.
- Updates packages via `apt`
- Removes unused packages
- Logs all output to `/var/log/sys-maintenance.log`

➡️ `cd 1-system-maintenance && sudo bash update.sh`

---

### 2. 👤 **User Creation Script with SSH Setup** (Python)
Creates a new user account with SSH access and secure permissions.
- Creates user with no password login
- Copies existing `authorized_keys` file
- Sets correct file and folder ownerships

➡️ `cd 2-user-management && sudo python3 create_user.py`

---

### 3. 🐳 **Docker Auto-Deployment Script** (Bash)
Automates Docker image update, stops the old container, and runs the latest image.
- Pulls latest image
- Stops and removes existing container
- Runs new container with exposed ports

➡️ `cd 3-docker-deployment && bash deploy_docker.sh`

---

### 4. ☁️ **AWS EC2 Auto Backup Script** (Python)
Creates snapshots of EC2 volumes with `Backup=True` tag using Boto3.
- Tag-based volume selection
- Snapshot creation with timestamp
- Custom tagging of snapshots for organization

➡️ `cd 4-aws-ec2-backup && python3 ec2_backup.py`

---

## ✅ Requirements

### System Scripts:
- Bash 5+
- Ubuntu/Debian-based system

### Python Scripts:
- Python 3.6+
- Modules: `boto3`, `subprocess`
- AWS credentials set via `~/.aws/credentials` or IAM role

---

## 📌 Security Best Practices Used
- Logs stored in secure locations
- SSH and user management with permission hardening
- Cloud backup follows tag-based policies
- Docker deployments are isolated and clean

---

## 📬 Contact

If you're interested in collaborating or have questions about any script:

**Henok Eshetu**  
💼 Cybersecurity & System Engineer  
📧 [your-email@example.com]  
🔗 [LinkedIn](https://linkedin.com/in/your-profile)  
🐙 [GitHub](https://github.com/HenokEshetu/Portfolio)

---

## ⭐ Contributions

Feel free to fork this repository or suggest improvements through pull requests or issues.

---

## 📄 License

MIT License – Use freely with attribution.

