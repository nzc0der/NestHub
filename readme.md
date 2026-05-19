# Family Dashboard

A premium, self-hosted family dashboard designed to run on a Raspberry Pi. Organize your family life with task management, shopping lists, shared calendars, and shared notes, all within a private, secure interface.

## Table of Contents

1. [Features](#features)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [First-Run Setup](#first-run-setup)
5. [Configuring the systemd Service](#configuring-the-systemd-service)
6. [Accessing the Dashboard](#accessing-the-dashboard)
7. [Backup and Recovery](#backup-and-recovery)
8. [Safe Manual Reset](#safe-manual-reset)
9. [Troubleshooting](#troubleshooting)
10. [License](#license)

## Features

- **Bento-style User Interface**: A modern, responsive dashboard layout optimized for both desktop and mobile devices.
- **Shared Calendar**: Coordinate family events and appointments with a centralized calendar system.
- **Shopping List**: Collaborative management for household essentials and groceries.
- **Notes System**: Secure, shared notes with full Markdown support for structured information.
- **Family Status Board**: Monitor the availability and status of family members in real-time.
- **Self-Hosted Privacy**: All data is stored locally on your Raspberry Pi, ensuring complete privacy and control.

## System Requirements

| Requirement | Version / Notes |
|-------------|-----------------|
| **Hardware** | Raspberry Pi 4, 400, or 5 recommended |
| **Operating System** | Raspberry Pi OS (64-bit recommended) |
| **Python** | 3.11 or later |
| **Git** | Required for updates and version control |
| **Network** | Local Wi-Fi or Ethernet connection |

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/nzc0der/FamilySystem.git
   cd FamilySystem
   ```

2. **Run the setup script**:
   The setup script creates a virtual environment, installs necessary dependencies, and initializes the configuration.
   ```bash
   python3 setup.py
   ```

## First-Run Setup

Following the initial setup, configure the administrative user and system parameters.
1. Start the server: `python3 server.py`
2. Navigate to the address displayed in the terminal via a web browser.
3. Complete the on-screen wizard to establish the primary family account.

## Configuring the systemd Service

To ensure the dashboard initiates automatically upon system boot:

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

## Accessing the Dashboard

Access the dashboard from any device on the local network:
- **URL**: `http://<your-pi-ip>:5000`
- **Default Port**: 5000 (configurable during setup)

## Backup and Recovery

The system includes an automated backup mechanism. Backups are preserved in the `backups/` directory.

- **Manual Backup**: Execute `python3 server.py --backup`
- **Restore**: Utilize the `reset_system.py` tool to restore the database from a specific snapshot.

## Safe Manual Reset

To reinitialize the system and clear all existing data:
```bash
python3 reset_system.py
```
*Note: This action will permanently delete all user data and configurations.*

## Troubleshooting

- **Port Conflict**: Verify if another instance is running or modify the port in the configuration.
- **Permission Issues**: Ensure the user has appropriate read/write permissions for the project directory.
- **Missing Dependencies**: Re-execute `pip install -r requirements.txt` within the virtual environment.

## License

Distributed under the MIT License. Refer to the `LICENSE` file for further details.
