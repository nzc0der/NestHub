#  Family Dashboard

![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-pink)
![Python](https://img.shields.io/badge/python-3.11+-blue)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](https://github.com/nzc0der/FamilySystem/blob/main/LICENSE)
![Status](https://img.shields.io/badge/status-active-success)
![Maintenance](https://img.shields.io/badge/maintained-yes-brightgreen)
[![HTML5](https://img.shields.io/badge/html5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://python.org)

A premium, self-hosted family dashboard designed to run on a Raspberry Pi. Organize your family life with task management, shopping lists, shared calendars, and shared notes—all in one private, secure interface.

---

## Table of Contents

1. [ Features](#features)
2. [ System Requirements](#system-requirements)
3. [ Installation](#installation)
4. [ First-Run Setup](#first-run-setup)
5. [ Configuring the systemd Service](#configuring-the-systemd-service)
6. [ Accessing the Dashboard](#accessing-the-dashboard)
7. [ Backup & Recovery](#backup--recovery)
8. [ Safe Manual Reset](#safe-manual-reset)
9. [ Troubleshooting](#troubleshooting)

---

##  Features

- **Bento-style UI**: A modern, responsive dashboard layout.
- **Shared Calendar**: Keep track of family events and appointments.
- **Shopping List**: Collaborative list for groceries and essentials.
- **Notes System**: Secure, shared notes with Markdown support.
- **Family Status Board**: Track member availability at a glance.
- **Self-Hosted**: Your data stays in your home on your Raspberry Pi.

---

##  System Requirements

| Requirement         | Version / Notes                               |
|---------------------|-----------------------------------------------|
| **Hardware**        | Raspberry Pi 4, 400, or 5 (recommended)       |
| **Operating System**| Raspberry Pi OS (64-bit recommended)          |
| **Python**          | 3.11 or later                                 |
| **Git**             | For updates and version control               |
| **Network**         | Local Wi-Fi or Ethernet                       |

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/nzc0der/FamilySystem.git
   cd FamilySystem
   ```

2. **Run the setup script**:
   The setup script will create a virtual environment, install dependencies, and prepare the configuration.
   ```bash
   python3 setup.py
   ```

---

##  First-Run Setup

After running the setup script, you will need to configure your admin user and basic settings.
1. Run the server: `python3 server.py`
2. Open your browser and navigate to the address shown in the terminal.
3. Follow the on-screen wizard to create your primary family account.

---

##  Configuring the systemd Service

To ensure the dashboard starts automatically when your Pi boots:

1. Copy the service file:
   ```bash
   sudo cp family_dashboard.service /etc/systemd/system/
   ```
2. Reload systemd and enable the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable family_dashboard.service
   sudo systemctl start family_dashboard.service
   ```

---

##  Accessing the Dashboard

Once running, access the dashboard from any device on your local network:
- **URL**: `http://<your-pi-ip>:8000`
- **Default Port**: 8000 (configurable in `config.json`)

---

##  Backup & Recovery

The dashboard includes an automated backup system. Backups are stored in the `backups/` directory.

- **Manual Backup**: Run `python3 server.py --backup`
- **Restore**: Use the `reset_system.py` tool to restore from a specific snapshot.

---

##  Safe Manual Reset

If you need to wipe the system and start fresh:
```bash
python3 reset_system.py
```
*Warning: This will delete all user data and settings.*

---

##  Troubleshooting

- **Port already in use**: Check if another instance is running or change the port in `config.json`.
- **Permission Denied**: Ensure you have read/write permissions in the project folder.
- **Missing Dependencies**: Re-run `pip install -r requirements.txt` within your virtual environment.

---

##  License

Distributed under the MIT License. See `LICENSE` for more information.
