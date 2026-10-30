import os
import time
import json
import urllib.request
import urllib.error
from datetime import datetime, date
from flask import Blueprint, jsonify, request, Response
from backend.database.db import query_db

tv_bp = Blueprint('tv', __name__)

# Weather cache storage
_weather_cache = {
    'timestamp': 0,
    'data': None
}

# Ormond, Melbourne, Victoria, Australia coordinates
DEFAULT_LAT = -37.9044
DEFAULT_LON = 145.0396
DEFAULT_TIMEZONE = "Australia/Melbourne"
WEATHER_CACHE_SECONDS = 900  # 15 minutes cache

def get_target_family_id():
    """
    Returns the target family ID for the TV dashboard.
    Can be configured via TV_FAMILY_ID environment variable or defaults to the first available family.
    """
    env_fid = os.environ.get('TV_FAMILY_ID')
    if env_fid:
        try:
            return int(env_fid)
        except ValueError:
            pass
    first_family = query_db("SELECT id FROM families ORDER BY id ASC LIMIT 1", one=True)
    if first_family:
        return first_family['id']
    return None

@tv_bp.route('/summary', methods=['GET'])
def get_tv_summary():
    """
    Aggregates useful family data for the TV dashboard in a single, fast request.
    No login required for local TV dashboard view, scoped to target family.
    """
    family_id = request.args.get('family_id')
    if not family_id:
        family_id = get_target_family_id()
    else:
        try:
            family_id = int(family_id)
        except ValueError:
            family_id = get_target_family_id()

    if not family_id:
        return jsonify({
            "configured": False,
            "message": "No family registered in NestHub yet. Please set up a family via the mobile app first.",
            "calendar": [],
            "chores": [],
            "meals": [],
            "grocery": [],
            "notes": [],
            "pet_care": [],
            "recent_messages": [],
            "stats": {}
        })

    family = query_db("SELECT id, name FROM families WHERE id = ?", (family_id,), one=True)
    if not family:
        return jsonify({"error": "Family not found", "configured": False}), 404

    # 1. Calendar events (upcoming or today, ordered by start_time)
    events = query_db("""
        SELECT e.*, u.username as assigned_to_name
        FROM events e
        LEFT JOIN users u ON e.assigned_to_id = u.id
        WHERE e.family_id = ?
        ORDER BY e.start_time ASC
        LIMIT 10
    """, (family_id,))

    # 2. Chores (pending or in_progress, ordered by priority and due_date)
    chores = query_db("""
        SELECT c.*, u.username as assigned_to_name
        FROM chores c
        LEFT JOIN users u ON c.assigned_to_id = u.id
        WHERE c.family_id = ? AND c.status != 'approved'
        ORDER BY
            CASE c.priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
                ELSE 4
            END ASC,
            c.due_date ASC
        LIMIT 10
    """, (family_id,))

    # 3. Meals (all meals organized for the week)
    meals = query_db("""
        SELECT * FROM meals
        WHERE family_id = ?
        ORDER BY
            CASE day_of_week
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
                ELSE 8
            END ASC
    """, (family_id,))

    # 4. Grocery list (active items)
    grocery = query_db("""
        SELECT * FROM grocery_items
        WHERE family_id = ? AND status IN ('active', 'collected')
        ORDER BY status ASC, id DESC
        LIMIT 12
    """, (family_id,))

    # 5. Sticky notes
    notes = query_db("""
        SELECT * FROM notes
        WHERE family_id = ?
        ORDER BY updated_at DESC
        LIMIT 4
    """, (family_id,))

    # 6. Pet care updates
    pet_care = query_db("""
        SELECT p.*, u.username as logged_by_name
        FROM pet_care p
        LEFT JOIN users u ON p.logged_by_id = u.id
        WHERE p.family_id = ?
        ORDER BY p.timestamp DESC
        LIMIT 5
    """, (family_id,))

    # 7. Recent messages/announcements
    messages = query_db("""
        SELECT m.*, u.username as sender_name
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.family_id = ?
        ORDER BY m.created_at DESC
        LIMIT 5
    """, (family_id,))

    # 8. Quick stats
    pending_chores = query_db("SELECT COUNT(*) as count FROM chores WHERE family_id = ? AND status != 'approved'", (family_id,), one=True)['count']
    active_grocery = query_db("SELECT COUNT(*) as count FROM grocery_items WHERE family_id = ? AND status = 'active'", (family_id,), one=True)['count']
    members_count = query_db("SELECT COUNT(*) as count FROM users WHERE family_id = ?", (family_id,), one=True)['count']

    # Latest activity timestamp to facilitate cache/polling checks
    latest_activity = query_db("SELECT timestamp FROM activity_logs WHERE family_id = ? ORDER BY timestamp DESC LIMIT 1", (family_id,), one=True)
    last_updated = latest_activity['timestamp'] if latest_activity else datetime.now().isoformat()

    return jsonify({
        "configured": True,
        "family": {
            "id": family['id'],
            "name": family['name']
        },
        "calendar": [dict(e) for e in events],
        "chores": [dict(c) for c in chores],
        "meals": [dict(m) for m in meals],
        "grocery": [dict(g) for g in grocery],
        "notes": [dict(n) for n in notes],
        "pet_care": [dict(p) for p in pet_care],
        "recent_messages": [dict(msg) for msg in messages],
        "stats": {
            "pending_chores": pending_chores,
            "active_grocery": active_grocery,
            "members_count": members_count
        },
        "last_updated": last_updated,
        "server_time": datetime.now().isoformat()
    })


@tv_bp.route('/weather', methods=['GET'])
def get_weather():
    """
    Fetches and caches weather for Ormond, Melbourne, Victoria, Australia.
    Uses Open-Meteo's free weather API with reliable in-memory caching.
    """
    lat = float(os.environ.get('WEATHER_LAT', DEFAULT_LAT))
    lon = float(os.environ.get('WEATHER_LON', DEFAULT_LON))
    tz = os.environ.get('WEATHER_TIMEZONE', DEFAULT_TIMEZONE)
    location_name = os.environ.get('WEATHER_LOCATION_NAME', "Ormond, Melbourne")

    now = time.time()
    if _weather_cache['data'] and (now - _weather_cache['timestamp'] < WEATHER_CACHE_SECONDS):
        return jsonify({
            **_weather_cache['data'],
            "cached": True,
            "cache_age_seconds": int(now - _weather_cache['timestamp'])
        })

    api_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&timezone={tz}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max"
        f"&forecast_days=6"
    )

    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'NestHub-TV/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            raw_data = json.loads(response.read().decode('utf-8'))

        # Weather code translation (WMO standards)
        wmo_codes = {
            0: ("Clear sky", "sun"),
            1: ("Mainly clear", "sun"),
            2: ("Partly cloudy", "cloud-sun"),
            3: ("Overcast", "cloud"),
            45: ("Fog", "smog"),
            48: ("Depositing rime fog", "smog"),
            51: ("Light drizzle", "cloud-rain"),
            53: ("Moderate drizzle", "cloud-rain"),
            55: ("Dense drizzle", "cloud-showers-heavy"),
            61: ("Slight rain", "cloud-rain"),
            63: ("Moderate rain", "cloud-showers-heavy"),
            65: ("Heavy rain", "cloud-showers-heavy"),
            71: ("Slight snow", "snowflake"),
            73: ("Moderate snow", "snowflake"),
            75: ("Heavy snow", "snowflake"),
            80: ("Slight rain showers", "cloud-sun-rain"),
            81: ("Moderate rain showers", "cloud-sun-rain"),
            82: ("Violent rain showers", "cloud-showers-heavy"),
            95: ("Thunderstorm", "bolt"),
            96: ("Thunderstorm with hail", "bolt"),
            99: ("Heavy thunderstorm", "bolt")
        }

        current = raw_data.get('current', {})
        daily = raw_data.get('daily', {})

        curr_code = current.get('weather_code', 0)
        curr_condition, curr_icon = wmo_codes.get(curr_code, ("Clear", "sun"))

        # Today's high/low
        today_max = daily.get('temperature_2m_max', [0])[0] if daily.get('temperature_2m_max') else 0
        today_min = daily.get('temperature_2m_min', [0])[0] if daily.get('temperature_2m_min') else 0
        today_rain_prob = daily.get('precipitation_probability_max', [0])[0] if daily.get('precipitation_probability_max') else 0

        # Forecast days (next 5 days)
        forecast = []
        dates = daily.get('time', [])
        max_temps = daily.get('temperature_2m_max', [])
        min_temps = daily.get('temperature_2m_min', [])
        codes = daily.get('weather_code', [])
        rain_probs = daily.get('precipitation_probability_max', [])

        for i in range(1, min(len(dates), 6)):
            d_code = codes[i] if i < len(codes) else 0
            cond, icon = wmo_codes.get(d_code, ("Clear", "sun"))
            forecast.append({
                "date": dates[i],
                "temp_max": round(max_temps[i]) if i < len(max_temps) else 0,
                "temp_min": round(min_temps[i]) if i < len(min_temps) else 0,
                "condition": cond,
                "icon": icon,
                "rain_probability": rain_probs[i] if i < len(rain_probs) else 0
            })

        processed_weather = {
            "location": location_name,
            "current": {
                "temperature": round(current.get('temperature_2m', 0)),
                "apparent_temperature": round(current.get('apparent_temperature', 0)),
                "humidity": current.get('relative_humidity_2m', 0),
                "condition": curr_condition,
                "icon": curr_icon,
                "wind_speed": round(current.get('wind_speed_10m', 0)),
                "today_max": round(today_max),
                "today_min": round(today_min),
                "rain_probability": today_rain_prob
            },
            "forecast": forecast,
            "last_updated": datetime.now().isoformat()
        }

        _weather_cache['timestamp'] = now
        _weather_cache['data'] = processed_weather

        return jsonify({
            **processed_weather,
            "cached": False
        })

    except Exception as e:
        # If cache exists, return stale cache gracefully on error
        if _weather_cache['data']:
            return jsonify({
                **_weather_cache['data'],
                "cached": True,
                "stale": True,
                "warning": f"Weather API error: {str(e)}"
            })
        # Default fallback so TV UI never crashes
        return jsonify({
            "location": location_name,
            "current": {
                "temperature": 21,
                "apparent_temperature": 21,
                "humidity": 55,
                "condition": "Partly cloudy",
                "icon": "cloud-sun",
                "wind_speed": 12,
                "today_max": 24,
                "today_min": 15,
                "rain_probability": 10
            },
            "forecast": [
                {"date": "Tomorrow", "temp_max": 23, "temp_min": 14, "condition": "Sunny", "icon": "sun", "rain_probability": 0},
                {"date": "Day 2", "temp_max": 22, "temp_min": 13, "condition": "Partly cloudy", "icon": "cloud-sun", "rain_probability": 10},
                {"date": "Day 3", "temp_max": 20, "temp_min": 12, "condition": "Showers", "icon": "cloud-rain", "rain_probability": 60},
                {"date": "Day 4", "temp_max": 19, "temp_min": 11, "condition": "Cloudy", "icon": "cloud", "rain_probability": 20},
                {"date": "Day 5", "temp_max": 21, "temp_min": 12, "condition": "Sunny", "icon": "sun", "rain_probability": 5}
            ],
            "fallback": True,
            "error": str(e),
            "last_updated": datetime.now().isoformat()
        })


from flask import current_app

@tv_bp.route('/stream')
def sse_stream():
    """
    Server-Sent Events (SSE) stream for real-time TV dashboard notifications.
    Emits heartbeat pings and detects changes in activity logs within app context.
    """
    family_id = request.args.get('family_id')
    if not family_id:
        family_id = get_target_family_id()
    else:
        try:
            family_id = int(family_id)
        except ValueError:
            family_id = get_target_family_id()

    app_instance = current_app._get_current_object()

    def event_stream():
        with app_instance.app_context():
            last_log_id = None
            if family_id:
                row = query_db("SELECT id FROM activity_logs WHERE family_id = ? ORDER BY id DESC LIMIT 1", (family_id,), one=True)
                if row:
                    last_log_id = row['id']

            yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'server_time': datetime.now().isoformat()})}\n\n"

            while True:
                time.sleep(5)
                if family_id:
                    latest = query_db("SELECT id, action, category, details FROM activity_logs WHERE family_id = ? ORDER BY id DESC LIMIT 1", (family_id,), one=True)
                    if latest and latest['id'] != last_log_id:
                        last_log_id = latest['id']
                        payload = {
                            "action": latest['action'],
                            "category": latest['category'],
                            "details": latest['details'],
                            "timestamp": datetime.now().isoformat()
                        }
                        yield f"event: update\ndata: {json.dumps(payload)}\n\n"
                    else:
                        yield f"event: ping\ndata: {json.dumps({'time': datetime.now().isoformat()})}\n\n"
                else:
                    yield f"event: ping\ndata: {json.dumps({'time': datetime.now().isoformat()})}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")
