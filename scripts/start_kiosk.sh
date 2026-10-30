#!/usr/bin/env bash
# ==============================================================================
# NestHub TV Companion Dashboard - Chromium Kiosk Launcher
# Designed for Raspberry Pi 400 connected to Panasonic TV
# ==============================================================================

set -u

# Ensure DISPLAY environment variable is set for X11 session
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

# Configuration
DASHBOARD_URL="${NESHUB_DASHBOARD_URL:-http://localhost:8000/dashboard}"
BACKEND_HEALTH_URL="${NESHUB_HEALTH_URL:-http://localhost:8000/api/tv/summary}"
MAX_WAIT_SECONDS=45
CACHE_DIR="/tmp/chromium-kiosk-cache"
PROFILE_DIR="/tmp/chromium-kiosk-profile"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting NestHub TV Kiosk launcher..."

# 1. Screen Power Management & Blanking Prevention
# Prevent TV screen blanking, screensavers, and DPMS sleep
if command -v xset >/dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Disabling screen blanking & DPMS..."
    xset s noblank 2>/dev/null || true
    xset s off 2>/dev/null || true
    xset -dpms 2>/dev/null || true
fi

# Hide mouse cursor when idle if unclutter is installed
if command -v unclutter >/dev/null 2>&1; then
    pkill unclutter 2>/dev/null || true
    unclutter -idle 0.5 -root &
fi

# 2. Wait for NestHub backend server to become available
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting for NestHub backend at ${BACKEND_HEALTH_URL}..."
START_TIME=$(date +%s)
while true; do
    if curl -s -f -o /dev/null --connect-timeout 2 "${BACKEND_HEALTH_URL}"; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] NestHub backend is online and ready!"
        break
    fi

    ELAPSED=$(( $(date +%s) - START_TIME ))
    if [ "$ELAPSED" -ge "$MAX_WAIT_SECONDS" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Warning: Backend wait timed out after ${MAX_WAIT_SECONDS}s. Launching Chromium anyway (offline recovery will handle reconnect)..."
        break
    fi

    sleep 1
done

# 3. Clean up previous crash state flags to prevent "Restore session?" prompt
mkdir -p "$CACHE_DIR" "$PROFILE_DIR"
find "$PROFILE_DIR" -name "Preferences" -exec sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' {} + 2>/dev/null || true
find "$PROFILE_DIR" -name "Preferences" -exec sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' {} + 2>/dev/null || true

# Determine Chromium executable name (varies between Raspbian/Debian/Ubuntu)
CHROMIUM_BIN=""
for bin in chromium-browser chromium google-chrome; do
    if command -v "$bin" >/dev/null 2>&1; then
        CHROMIUM_BIN="$bin"
        break
    fi
done

if [ -z "$CHROMIUM_BIN" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Chromium browser is not installed. Please install it using: sudo apt-get install -y chromium-browser"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Using browser binary: $CHROMIUM_BIN"

# Raspberry Pi 400 Chromium Performance Flags
CHROME_FLAGS=(
    "--kiosk"
    "--noerrdialogs"
    "--disable-infobars"
    "--no-first-run"
    "--ozone-platform=x11"
    "--enable-features=OverlayScrollbar"
    "--fast"
    "--fast-start"
    "--disable-features=Translate"
    "--disable-background-networking"
    "--disable-component-update"
    "--disable-features=OptimizationHints"
    "--disable-translate"
    "--disable-pinch"
    "--overscroll-history-navigation=0"
    "--disable-session-crashed-bubble"
    "--disk-cache-dir=$CACHE_DIR"
    "--user-data-dir=$PROFILE_DIR"
    "--check-for-update-interval=31536000"
    "--autoplay-policy=no-user-gesture-required"
    "--window-position=0,0"
    "--start-fullscreen"
    "$DASHBOARD_URL"
)

# 4. Supervised Crash Recovery Loop
# If Chromium exits unexpectedly, wait 2 seconds and relaunch automatically.
while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Launching Chromium Kiosk on $DASHBOARD_URL..."
    "$CHROMIUM_BIN" "${CHROME_FLAGS[@]}" 2>&1 | logger -t nesthub-kiosk || true
    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Chromium exited with code $EXIT_CODE. Relaunching in 3 seconds..."
    sleep 3
done
