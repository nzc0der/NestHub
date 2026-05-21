# NestHub | Premium Family Dashboard

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.1-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**NestHub** is a sophisticated, self-hosted family management ecosystem. Built with a robust Python/Flask backend and a stunning, mobile-first glassmorphic Single Page Application (SPA) frontend, it provides a unified interface for organizing your family's daily life.

---

## Core Features

### Family Organization
- **Unified Calendar**: Shared event tracking with a responsive grid view.
- **Smart Chores**: Points-based task management system with Parent/Admin approval workflow.
- **Dynamic Grocery List**: Real-time collaborative shopping list with role-based restrictions (children can collect, but only parents/admins can finalize purchases).
- **Meal Planner**: Weekly menu organization with automated categorization.

### Communication & Media
- **Family Chat**: Real-time messaging for family updates and coordinate.
- **Photo Gallery**: Share family memories with a moderated approval system for younger members.
- **Sticky Notes**: Digital board for quick reminders and shared notes.

### Advanced Tools
- **Pet Care Log**: Track feedings, walks, and health updates for family pets.
- **Emergency Hub**: Centralized access to critical contacts and information.
- **Admin Dashboard**: Comprehensive system statistics, activity logs, and real-time system health diagnostics.

---

## Technical Architecture

### Backend (Python/Flask)
- **Modular Design**: Blueprint-based routing for clean separation of concerns.
- **Security**: PBKDF2 password hashing via `bcrypt`, session-based authentication, and granular Role-Based Access Control (RBAC).
- **Database**: Optimized SQLite schema with transactional integrity and foreign key constraints.
- **Diagnostics**: Integrated system monitoring using `psutil`.

### Frontend (SPA)
- **Engine**: Vanilla JavaScript (ES6+) with a custom module-based routing system.
- **Styling**: Modern CSS3 using Flexbox, Grid, and advanced Glassmorphism effects.
- **Performance**: Asynchronous API interactions for a "desktop-class" web experience.
- **Responsiveness**: Mobile-first design that adapts seamlessly from handheld devices to wide desktop monitors.

---

## Installation & Deployment

### Local Development Setup

1. **Clone & Enter**:
   ```bash
   git clone https://github.com/nzc0der/NestHub.git
   cd NestHub
   ```

2. **Environment Setup**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Launch**:
   ```bash
   python3 backend/app.py
   ```
   *The system will automatically initialize the database on first run.*

---

## Remote Access with Tailscale

To access NestHub securely from anywhere in the world without complex port forwarding:

1. **Install Tailscale**: Download and install [Tailscale](https://tailscale.com/download) on your host machine (e.g., Raspberry Pi) and your mobile devices.
2. **Authenticate**: Log in on all devices.
3. **Get Tailscale IP**: Run `tailscale ip -4` on your host machine to get your private "Tailnet" IP (e.g., `100.x.y.z`).
4. **Access Anywhere**: Open `http://100.x.y.z:8000` in your browser on any device logged into your Tailscale account.
5. **MagicDNS (Optional)**: Enable MagicDNS in the Tailscale console to use your host's name (e.g., `http://raspberrypi:8000`) instead of the IP.

---

## Diagnostics & Troubleshooting

### Built-in Diagnostics
Admins can access the **Admin Panel** to view real-time metrics:
- CPU & Memory Load
- Disk Space Availability
- Detailed Activity Logs
- Process Uptime

### Manual Tests
Run the automated validation suite to ensure core logic is intact:
```bash
python3 backend/tests.py
```

### Common Issues
- **401 Unauthorized**: Ensure your session hasn't expired. Log out and log back in.
- **Database Locked**: Usually occurs during heavy concurrent write attempts. SQLite handles this gracefully with a retry, but ensure no other processes are accessing the `.db` file directly.
- **Frontend Assets Not Loading**: Verify that the `static_folder` path in `backend/app.py` correctly points to the `frontend/` directory relative to your execution path.

---

## License
NestHub is distributed under the **MIT License**. See `LICENSE` for details.

