# NestHub | Premium Family Dashboard & TV Companion

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.1-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**NestHub** is a self-hosted family management ecosystem and always-on smart-home TV dashboard. Built with a robust Python/Flask backend, it provides two complementary interfaces running simultaneously from a single host (such as a Raspberry Pi 400):

1. **Phone & Desktop Interface (`/`)**: A mobile-first glassmorphic Single Page Application (SPA) for managing calendar events, chores, groceries, meals, notes, pet logs, and family chat.
2. **TV Companion Dashboard (`/dashboard`)**: A fullscreen, read-only, 16:9 widescreen information display tailored for living room televisions (e.g. Panasonic VIERA connected via HDMI to a Raspberry Pi 400 in Chromium kiosk mode).

---

## Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                  Raspberry Pi 400                                 |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                     NestHub Backend (Flask / Python 3)                      |  |
|  |                                Port 8000                                    |  |
|  |                                                                             |  |
|  |  +-----------------------+     +--------------------+   +----------------+  |  |
|  |  |  Family Blueprints    |     |   TV Blueprint     |   | SQLite DB      |  |  |
|  |  |  /api/chores, meals,  |     |   /api/tv/summary  |---| family_hub.db  |  |  |
|  |  |  calendar, grocery... |     |   /api/tv/stream   |   +----------------+  |  |
|  |  +-----------------------+     |   /api/tv/weather  |                       |  |
|  +--------------|-----------------+---------|----------+-----------------------+  |
|                 |                           |                                     |
|                 |                           | (SSE / Local JSON Fetch)            |
|                 v                           v                                     |
|  +-----------------------------+  +--------------------------------------------+  |
|  |  Mobile / Desktop Web SPA   |  |        Chromium Kiosk Application          |  |
|  |       (frontend/)           |  |     (http://localhost:8000/dashboard)      |  |
|  +-----------------------------+  +---------------------|----------------------+  |
+-----------------|---------------------------------------|-------------------------+
                  |                                       |
                  | (Wi-Fi / LAN / Tailscale)             | (Micro-HDMI)
                  v                                       v
     +--------------------------+           +---------------------------+
     |   Family Mobile Phones   |           |  Panasonic Television     |
     |    & Laptops (Web SPA)   |           |  (Always-On 16:9 Display) |
     +--------------------------+           +---------------------------+
                                                          ^
                                                          |
                                            +---------------------------+
                                            | Open-Meteo Weather API    |
                                            | (Ormond, Melbourne, VIC)  |
                                            +---------------------------+
```

---

## Key Features

### 1. TV Companion Dashboard (`/dashboard`)
- **Large Digital Clock & Date**: High-visibility time displaying hours, minutes, and seconds, updating every second for Melbourne local time.
- **Ormond (Melbourne) Weather**: Live temperature, current weather conditions with animated icons, high/low range, humidity, wind speed, and 5-day daily forecast via Open-Meteo with 15-minute backend caching.
- **Real NestHub Information**:
  - **Upcoming Events**: Shared family calendar schedule with location and creator tags.
  - **Pending Chores**: Live chore queue with point values and assignees.
  - **Today's Menu**: Daily breakfast, lunch, and dinner plans.
  - **Grocery Needs**: Items waiting to be purchased.
  - **Family Noticeboard**: Sticky notes and reminders pinned for the household.
  - **Pet Care & Status**: Most recent pet feedings, walks, and system activity logs.
- **Real-Time Synchronisation**: Uses Server-Sent Events (SSE) via `/api/tv/stream` with resilient 20-second polling fallback.
- **Dynamic Backgrounds**: CSS gradient shifts automatically throughout the day:
  - *Morning (06:00 - 11:00)*: Soft sunrise pastels.
  - *Day (11:00 - 17:00)*: Crisp sky blue tones.
  - *Evening (17:00 - 21:00)*: Warm sunset amber.
  - *Night (21:00 - 06:00)*: Deep atmospheric navy.
- **Plasma / OLED / LCD Screen Protection**:
  - Subtle 1-2px CSS float animation prevents permanent element burn-in.
  - Automatic night dimming after 21:00 lowers overall backlight brightness.
  - Integrated full-black floating clock screensaver after 20 minutes of inactivity (wakes immediately on mouse move or keypress).
  - Offline banner indicators with automated reconnection retry loops.

### 2. Phone Interface (`/`)
- Mobile-first single-page application for family members.
- Role-based permissions (Parent, Child, Admin).
- Point-reward chore approvals, interactive meal planner, grocery checklist, chat, photo gallery, and emergency contacts.

---

## Hardware & Software Requirements

- **Host Device**: Raspberry Pi 400 (or Raspberry Pi 4 Model B, 2GB+ RAM recommended).
- **Display**: Any HDMI television (tested on Panasonic VIERA 1080p/720p).
- **Operating System**: Raspberry Pi OS (Debian 11 Bullseye or Debian 12 Bookworm) with desktop environment (X11 / Wayland).
- **Packages**: Python 3.10+, Chromium browser, `unclutter`, `x11-xserver-utils`.

---

## Installation & Setup

### 1. Install System Dependencies
On your Raspberry Pi terminal:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv chromium-browser unclutter x11-xserver-utils
```

### 2. Clone Repository & Setup Virtual Environment
```bash
cd ~
git clone https://github.com/nzc0der/NestHub.git
cd NestHub

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the template configuration:
```bash
cp .env.example .env
nano .env
```
*Review the default values. Melbourne weather coordinates (`-37.9044, 145.0396`) and port 8000 are pre-configured.*

### 4. Seed / Verify Database
Run the test suite to ensure the environment is ready:
```bash
python3 backend/tests.py
```

---

## Systemd Services & Automatic Startup

Two systemd services manage the backend and kiosk display independently.

### Service 1: NestHub Backend (`nesthub.service`)
1. Copy the service unit file to systemd:
   ```bash
   sudo cp services/nesthub.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable nesthub.service
   sudo systemctl start nesthub.service
   ```
2. Verify the backend is active:
   ```bash
   sudo systemctl status nesthub.service
   curl -I http://localhost:8000/api/tv/summary
   ```

### Service 2: Chromium Kiosk Mode

You can configure kiosk autostart using either the desktop session autostart (recommended for Raspberry Pi OS desktop) or the systemd user service.

#### Option A: Desktop Autostart (Recommended for X11 / Wayfire desktop)
```bash
mkdir -p ~/.config/autostart
cp services/nesthub-kiosk.desktop ~/.config/autostart/
chmod +x scripts/start_kiosk.sh
```

#### Option B: User Systemd Service
```bash
mkdir -p ~/.config/systemd/user/
cp services/nesthub-kiosk.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable nesthub-kiosk.service
systemctl --user start nesthub-kiosk.service
```

### 5. Accessing the Applications
- **Phone / Tablet Interface**: `http://<raspberrypi-ip>:8000/` or `http://raspberrypi.local:8000/`
- **TV Dashboard**: `http://<raspberrypi-ip>:8000/dashboard` or `http://raspberrypi.local:8000/dashboard`
- **Remote Access**: Connect devices via [Tailscale](https://tailscale.com/) to access `http://<tailscale-ip>:8000/` securely from anywhere.

---

## Configuration Options

Settings can be changed in `.env` without modifying code:

| Setting | Default Value | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | `dev_secret_key` | Flask cryptographic session key |
| `FLASK_PORT` | `8000` | Port on which the application listens |
| `DATABASE_PATH` | `database/family_hub.db` | Relative or absolute path to SQLite file |
| `LATITUDE` | `-37.9044` | Latitude for weather (default: Ormond, Melbourne) |
| `LONGITUDE` | `145.0396` | Longitude for weather (default: Ormond, Melbourne) |
| `LOCATION_NAME` | `Ormond, Melbourne` | Display name for weather badge |
| `TIMEZONE` | `Australia/Melbourne` | Timezone for weather API requests |

To change the kiosk display URL or screen resolution, adjust `DASHBOARD_URL` in `scripts/start_kiosk.sh`.

---

## Service Management & Helpful Commands

### Check Status
```bash
# Check backend server
sudo systemctl status nesthub.service

# Check kiosk process
systemctl --user status nesthub-kiosk.service  # if using user service
pgrep -af chromium-browser                     # if using desktop autostart
```

### View Live Logs
```bash
# Follow backend application logs
sudo journalctl -u nesthub.service -f

# Follow kiosk startup script logs
tail -f ~/.nesthub_kiosk.log
```

### Restart Services
```bash
# Restart backend without restarting the TV display
sudo systemctl restart nesthub.service

# Relaunch Chromium kiosk
killall chromium-browser  # start_kiosk.sh will immediately restart it cleanly
```

### Network Connectivity Check
```bash
# Verify backend responds
curl -s http://localhost:8000/api/tv/summary | jq .

# Verify Open-Meteo weather responds
curl -s "https://api.open-meteo.com/v1/forecast?latitude=-37.9044&longitude=145.0396&current_weather=true"
```

---

## Troubleshooting Guide

### 1. TV Displays a Blank Screen
- **What it looks like**: Panasonic TV shows "No Signal" or stays entirely black.
- **Possible Causes**: Micro-HDMI cable plugged into HDMI port 1 instead of HDMI port 0, incorrect HDMI output timing, or TV is on the wrong input.
- **Diagnostic Steps**:
  ```bash
  vcgencmd display_power
  # 1 = on, 0 = off
  ```
- **How to Fix**:
  1. Ensure the micro-HDMI cable is connected to the port closest to the USB-C power port (HDMI 0) on the Raspberry Pi 400.
  2. Switch TV input source to the matching HDMI port using the Panasonic remote.
  3. Force HDMI hotplug in `/boot/firmware/config.txt` (or `/boot/config.txt` on older OS) by adding:
     ```ini
     hdmi_force_hotplug=1
     hdmi_group=1
     hdmi_mode=16  # Forces 1080p 60Hz
     ```
  4. Reboot: `sudo reboot`.

---

### 2. Chromium Does Not Start
- **What it looks like**: Raspberry Pi boots into the desktop background, but Chromium never opens.
- **Possible Causes**: Missing executable permissions on `start_kiosk.sh`, missing packages (`unclutter`), or Chromium profile locks.
- **Diagnostic Steps**:
  ```bash
  cat ~/.nesthub_kiosk.log
  /home/pi/NestHub/scripts/start_kiosk.sh
  ```
- **How to Fix**:
  1. Make the kiosk script executable:
     ```bash
     chmod +x /home/pi/NestHub/scripts/start_kiosk.sh
     ```
  2. Ensure the display variable is set:
     ```bash
     export DISPLAY=:0
     ```
  3. Clean any corrupted browser locks:
     ```bash
     rm -rf ~/.config/chromium/Singleton*
     ```

---

### 3. Dashboard Does Not Load ("Connection Refused" / "Unable to Connect")
- **What it looks like**: Chromium shows "This site can't be reached" (`ERR_CONNECTION_REFUSED`).
- **Possible Causes**: `nesthub.service` failed to start or is still launching.
- **Diagnostic Steps**:
  ```bash
  sudo systemctl status nesthub.service
  sudo journalctl -u nesthub.service -n 50
  ```
- **How to Fix**:
  1. Check if another service is occupying port 8000:
     ```bash
     sudo lsof -i :8000
     ```
  2. Verify virtual environment path and permissions in `/etc/systemd/system/nesthub.service`.
  3. Manually start backend to view tracebacks:
     ```bash
     cd ~/NestHub && source venv/bin/activate && python3 backend/app.py
     ```

---

### 4. NestHub Backend is Unavailable / Disconnected Toast on TV
- **What it looks like**: The TV shows a bottom notification: *"Connection to NestHub lost. Retrying in background..."*.
- **Possible Causes**: Backend was restarted or crashed; SQLite file locked.
- **Diagnostic Steps**:
  ```bash
  curl -I http://localhost:8000/api/tv/summary
  ```
- **How to Fix**:
  1. The TV dashboard automatically retries reconnecting every 10 seconds via SSE and HTTP polling.
  2. If the backend crashed, check error logs: `sudo journalctl -u nesthub.service -e`.
  3. Restart the service: `sudo systemctl restart nesthub.service`. The TV will re-sync immediately once the server is back online.

---

### 5. Weather Information is Missing / Shows Fallback
- **What it looks like**: Current weather displays "Unavailable" or defaults to 20°C with empty forecast cards.
- **Possible Causes**: Raspberry Pi has lost internet access or Open-Meteo API is unreachable.
- **Diagnostic Steps**:
  ```bash
  ping -c 3 8.8.8.8
  curl -s "https://api.open-meteo.com/v1/forecast?latitude=-37.9044&longitude=145.0396&current_weather=true" | head -n 10
  ```
- **How to Fix**:
  1. Check Wi-Fi/Ethernet connectivity on the Raspberry Pi:
     ```bash
     nmcli device status
     ```
  2. Verify DNS resolution: `cat /etc/resolv.conf`.
  3. Once network connectivity is restored, the backend cache automatically refreshes on the next cycle.

---

### 6. Dashboard Information is Not Updating
- **What it looks like**: Chores or calendar events changed on the phone do not reflect on the TV screen.
- **Possible Causes**: EventSource (SSE) stream closed and failed to fall back; browser thread paused.
- **Diagnostic Steps**:
  - Check the bottom-right connection pill on the TV dashboard. If it shows *"Polling (backup)"* or *"Reconnecting"*, the SSE connection dropped.
- **How to Fix**:
  1. Verify SSE endpoint returns events:
     ```bash
     curl -N http://localhost:8000/api/tv/stream
     ```
  2. The TV dashboard has a built-in 20-second active polling fallback if SSE is disconnected.
  3. Force a reload by restarting Chromium: `killall chromium-browser`.

---

### 7. Chromium Crashes or Closes Unexpectedly
- **What it looks like**: TV flashes back to desktop or terminal screen.
- **Possible Causes**: Out of memory (OOM), GPU memory starvation on the Raspberry Pi.
- **Diagnostic Steps**:
  ```bash
  dmesg -T | grep -i oom
  vcgencmd get_mem gpu
  ```
- **How to Fix**:
  1. `start_kiosk.sh` runs inside an infinite restart loop; it will relaunch Chromium automatically within 3 seconds.
  2. Allocate at least 128MB to the GPU in `/boot/firmware/config.txt`:
     ```ini
     gpu_mem=128
     ```
  3. Ensure flags in `scripts/start_kiosk.sh` (`--disable-features=TranslateUI`, `--disk-cache-size=33554432`) are active to minimise memory footprint.

---

### 8. Dashboard Does Not Start After Reboot
- **What it looks like**: After rebooting, only desktop icons appear; no dashboard.
- **Possible Causes**: Service or desktop autostart entry is not enabled.
- **Diagnostic Steps**:
  ```bash
  systemctl is-enabled nesthub.service
  ls -l ~/.config/autostart/nesthub-kiosk.desktop
  ```
- **How to Fix**:
  1. Enable the backend systemd service:
     ```bash
     sudo systemctl enable nesthub.service
     ```
  2. Verify autostart file permissions:
     ```bash
     chmod +x ~/.config/autostart/nesthub-kiosk.desktop
     ```
  3. Check user autologin: in `sudo raspi-config`, choose `System Options` > `Boot / Auto Login` > `Desktop Autologin`.

---

### 9. Raspberry Pi Runs Slowly or High CPU
- **What it looks like**: Choppy clock seconds animation or slow dashboard rendering.
- **Possible Causes**: Software rendering instead of hardware acceleration, runaway background jobs.
- **Diagnostic Steps**:
  ```bash
  htop
  chromium-browser --version
  ```
- **How to Fix**:
  1. Ensure hardware acceleration flags are present in `scripts/start_kiosk.sh`:
     `--enable-gpu-rasterization --enable-zero-copy`.
  2. Disable unused background daemons.
  3. Check CPU temperature to rule out thermal throttling:
     ```bash
     vcgencmd measure_temp
     ```

---

### 10. TV Resolution or Overscan Problems
- **What it looks like**: Edges of the dashboard are cut off (top clock truncated, bottom footer cut off) or black borders surround the screen.
- **Possible Causes**: Television overscan active on old Panasonic TV.
- **Diagnostic Steps**:
  - Look at the footer: "Panasonic VIERA • Raspberry Pi 400". If this line is partially cut off, overscan is enabled.
- **How to Fix**:
  1. **TV Menu Method (Best)**: On the Panasonic remote, press **Menu** > **Picture** > **Advanced Settings** > Set **16:9 Overscan** to **Off** (or set Aspect Ratio to **Just Scan** / **Full / 1:1**).
  2. **Raspberry Pi Method**: In `/boot/firmware/config.txt` (or `/boot/config.txt`):
     ```ini
     disable_overscan=1
     ```
     Or manually tune overscan offsets:
     ```ini
     overscan_left=16
     overscan_right=16
     overscan_top=16
     overscan_bottom=16
     ```
  3. Reboot: `sudo reboot`.

---

## Maintenance & Backups

### Updating the Application
To pull updates safely without disrupting family data:
```bash
cd ~/NestHub
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart nesthub.service
```

### Backing Up Configuration & Database
All dynamic data resides in `database/family_hub.db` and user configuration in `.env`.
```bash
# Create a timestamped backup
mkdir -p ~/nesthub_backups
tar -czvf ~/nesthub_backups/nesthub_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  ~/NestHub/database/family_hub.db \
  ~/NestHub/.env
```

### Restoring from Backup
```bash
sudo systemctl stop nesthub.service
tar -xzvf ~/nesthub_backups/nesthub_backup_YYYYMMDD_HHMMSS.tar.gz -C /
sudo systemctl start nesthub.service
```

---

## License
NestHub is distributed under the **MIT License**. See `LICENSE` for details.
