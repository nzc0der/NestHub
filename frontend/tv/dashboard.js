/**
 * NestHub TV Companion Dashboard Script
 * Optimized for Raspberry Pi 400 & Panasonic 16:9 Display
 */

(function () {
    'use strict';

    // Application State
    const state = {
        lastSummaryTime: 0,
        weather: null,
        summary: null,
        isOnline: true,
        inactivityTimer: null,
        screensaverActive: false,
        screensaverTimeout: 20 * 60 * 1000 // 20 minutes before screensaver activates
    };

    // DOM Elements Cache
    const el = {
        clockTime: document.getElementById('clock-time'),
        clockDay: document.getElementById('clock-day'),
        clockDate: document.getElementById('clock-date'),
        familyName: document.getElementById('family-name'),
        weatherTemp: document.getElementById('weather-temp'),
        weatherDesc: document.getElementById('weather-desc'),
        weatherIcon: document.getElementById('weather-icon'),
        weatherRain: document.getElementById('weather-rain'),
        weatherWind: document.getElementById('weather-wind'),
        weatherRange: document.getElementById('weather-range'),
        forecastGrid: document.getElementById('forecast-grid'),
        eventsList: document.getElementById('events-list'),
        eventsCount: document.getElementById('events-count'),
        mealsList: document.getElementById('meals-list'),
        todayDayLabel: document.getElementById('today-day-label'),
        choresList: document.getElementById('chores-list'),
        choresCount: document.getElementById('chores-count'),
        groceryList: document.getElementById('grocery-list'),
        groceryCount: document.getElementById('grocery-count'),
        notesList: document.getElementById('notes-list'),
        notesCount: document.getElementById('notes-count'),
        petcareList: document.getElementById('petcare-list'),
        lastSyncTime: document.getElementById('last-sync-time'),
        connStatus: document.getElementById('connection-status'),
        toastOffline: document.getElementById('toast-offline'),
        screensaverOverlay: document.getElementById('screensaver-overlay'),
        screensaverClock: document.getElementById('screensaver-clock'),
        screensaverDate: document.getElementById('screensaver-date'),
        screensaverWeather: document.getElementById('screensaver-weather')
    };

    // =========================================================================
    // 1. Clock, Date, Timezone & Dynamic Themes
    // =========================================================================
    function updateClock() {
        // Melbourne, Victoria, Australia Timezone
        const now = new Date();
        const melbourneFormatter = new Intl.DateTimeFormat('en-AU', {
            timeZone: 'Australia/Melbourne',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });

        const melbourneParts = melbourneFormatter.formatToParts(now);
        const timeMap = Object.fromEntries(melbourneParts.map(p => [p.type, p.value]));
        const timeStr = `${timeMap.hour}:${timeMap.minute}:${timeMap.second}`;

        if (el.clockTime) el.clockTime.textContent = timeStr;

        // Date & Day
        const dayFormatter = new Intl.DateTimeFormat('en-AU', {
            timeZone: 'Australia/Melbourne',
            weekday: 'long'
        });
        const dateFormatter = new Intl.DateTimeFormat('en-AU', {
            timeZone: 'Australia/Melbourne',
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });

        const dayStr = dayFormatter.format(now);
        const dateStr = dateFormatter.format(now);

        if (el.clockDay) el.clockDay.textContent = dayStr;
        if (el.clockDate) el.clockDate.textContent = dateStr;
        if (el.todayDayLabel) el.todayDayLabel.textContent = dayStr;

        // Screensaver clock update
        if (state.screensaverActive) {
            if (el.screensaverClock) el.screensaverClock.textContent = `${timeMap.hour}:${timeMap.minute}`;
            if (el.screensaverDate) el.screensaverDate.textContent = `${dayStr}, ${dateStr}`;
        }

        // Apply Time-of-day dynamic theme
        applyTimeOfDayTheme(parseInt(timeMap.hour, 10));
    }

    function applyTimeOfDayTheme(hour) {
        const body = document.body;
        body.classList.remove('theme-morning', 'theme-day', 'theme-evening', 'theme-night');

        if (hour >= 5 && hour < 11) {
            body.classList.add('theme-morning');
        } else if (hour >= 11 && hour < 17) {
            body.classList.add('theme-day');
        } else if (hour >= 17 && hour < 21) {
            body.classList.add('theme-evening');
        } else {
            body.classList.add('theme-night');
        }
    }

    // =========================================================================
    // 2. Weather Fetch & Render (Ormond, Melbourne)
    // =========================================================================
    async function fetchWeather() {
        try {
            const res = await fetch('/api/tv/weather');
            if (!res.ok) throw new Error('Weather API HTTP status ' + res.status);
            const data = await res.json();
            state.weather = data;
            renderWeather(data);
        } catch (err) {
            console.warn('Weather fetch issue:', err);
            // If we have previous weather data, keep it; otherwise UI has fallback defaults
        }
    }

    function renderWeather(data) {
        if (!data || !data.current) return;
        const cur = data.current;

        if (el.weatherTemp) el.weatherTemp.textContent = `${cur.temperature}°`;
        if (el.weatherDesc) el.weatherDesc.textContent = cur.condition;
        if (el.weatherRain) el.weatherRain.textContent = `${cur.rain_probability || 0}%`;
        if (el.weatherWind) el.weatherWind.textContent = `${cur.wind_speed} km/h`;
        if (el.weatherRange) el.weatherRange.textContent = `${cur.today_max}° / ${cur.today_min}°`;

        if (el.weatherIcon) {
            const iconClass = cur.icon || 'cloud-sun';
            el.weatherIcon.innerHTML = `<i class="fas fa-${iconClass}"></i>`;
        }

        if (el.screensaverWeather) {
            el.screensaverWeather.textContent = `${cur.temperature}° • ${cur.condition} • Ormond, Melbourne`;
        }

        // Render 5-day forecast
        if (el.forecastGrid && data.forecast && data.forecast.length > 0) {
            el.forecastGrid.innerHTML = data.forecast.slice(0, 5).map(f => {
                let dayName = f.date;
                try {
                    const parsed = new Date(f.date + 'T00:00:00');
                    dayName = parsed.toLocaleDateString('en-AU', { weekday: 'short' });
                } catch (e) {}

                return `
                    <div class="forecast-day-card">
                        <span class="forecast-date">${escapeHTML(dayName)}</span>
                        <div class="forecast-icon">
                            <i class="fas fa-${f.icon || 'sun'}"></i>
                        </div>
                        <div class="forecast-temps">
                            <span>${f.temp_max}°</span>
                            <span class="forecast-temp-min">/${f.temp_min}°</span>
                        </div>
                        <span class="forecast-rain"><i class="fas fa-droplet text-blue"></i> ${f.rain_probability}%</span>
                    </div>
                `;
            }).join('');
        }
    }

    // =========================================================================
    // 3. NestHub Data Fetch & Render
    // =========================================================================
    async function fetchSummary() {
        try {
            const res = await fetch('/api/tv/summary');
            if (!res.ok) throw new Error('Summary API HTTP status ' + res.status);
            const data = await res.json();
            state.summary = data;
            setOnlineStatus(true);
            renderSummary(data);

            const now = new Date();
            if (el.lastSyncTime) {
                el.lastSyncTime.textContent = now.toLocaleTimeString('en-AU', { hour: '2-digit', minute: '2-digit' });
            }
        } catch (err) {
            console.warn('TV summary fetch error:', err);
            setOnlineStatus(false);
        }
    }

    function renderSummary(data) {
        if (!data || !data.configured) {
            if (el.familyName) el.familyName.textContent = 'Welcome to NestHub';
            if (el.eventsList) el.eventsList.innerHTML = '<div class="empty-state">No family set up yet</div>';
            if (el.choresList) el.choresList.innerHTML = '<div class="empty-state">No chores found</div>';
            if (el.mealsList) el.mealsList.innerHTML = '<div class="empty-state">No meals scheduled</div>';
            if (el.groceryList) el.groceryList.innerHTML = '<div class="empty-state">No grocery items</div>';
            return;
        }

        // Family Name
        if (el.familyName && data.family) {
            el.familyName.textContent = `${data.family.name} Family`;
        }

        // Calendar Events
        renderEvents(data.calendar || []);

        // Meals
        renderMeals(data.meals || []);

        // Chores
        renderChores(data.chores || []);

        // Grocery
        renderGrocery(data.grocery || []);

        // Notes
        renderNotes(data.notes || [], data.recent_messages || []);

        // Pet Care
        renderPetCare(data.pet_care || []);
    }

    function renderEvents(events) {
        if (!el.eventsList) return;
        if (el.eventsCount) el.eventsCount.textContent = `${events.length} upcoming`;

        if (events.length === 0) {
            el.eventsList.innerHTML = '<div class="empty-state"><i class="fas fa-calendar-check" style="margin-right:8px"></i> No upcoming events scheduled</div>';
            return;
        }

        el.eventsList.innerHTML = events.slice(0, 5).map(e => {
            let timeLabel = 'Upcoming';
            let relativeLabel = '';
            try {
                const dateObj = new Date(e.start_time);
                timeLabel = dateObj.toLocaleDateString('en-AU', { month: 'short', day: 'numeric' });
                relativeLabel = dateObj.toLocaleTimeString('en-AU', { hour: 'numeric', minute: '2-digit' });
            } catch (err) {
                timeLabel = e.start_time;
            }

            const assignee = e.assigned_to_name ? `<span class="chore-assigned"><i class="fas fa-user"></i> ${escapeHTML(e.assigned_to_name)}</span>` : '';
            const location = e.location ? `<span><i class="fas fa-location-dot"></i> ${escapeHTML(e.location)}</span>` : '';

            return `
                <div class="event-item">
                    <div class="event-time-badge">
                        <div>${escapeHTML(timeLabel)}</div>
                        <div style="font-size:10px; opacity:0.8">${escapeHTML(relativeLabel)}</div>
                    </div>
                    <div class="event-info">
                        <div class="event-title">${escapeHTML(e.title)}</div>
                        <div class="event-sub">
                            ${location}
                            ${assignee}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderMeals(meals) {
        if (!el.mealsList) return;

        // Current Melbourne day of week
        const todayDay = new Intl.DateTimeFormat('en-AU', {
            timeZone: 'Australia/Melbourne',
            weekday: 'long'
        }).format(new Date());

        const todayMeals = meals.filter(m => m.day_of_week.toLowerCase() === todayDay.toLowerCase());

        const mealTypes = ['Breakfast', 'Lunch', 'Dinner'];
        const mealsBySlot = {
            'Breakfast': 'None planned',
            'Lunch': 'None planned',
            'Dinner': 'None planned'
        };

        todayMeals.forEach(m => {
            const slot = mealTypes.find(t => t.toLowerCase() === m.meal_type.toLowerCase()) || m.meal_type;
            mealsBySlot[slot] = m.description || 'Planned';
        });

        el.mealsList.innerHTML = `
            <div class="meals-row">
                <div class="meal-block">
                    <span class="meal-type"><i class="fas fa-egg"></i> Breakfast</span>
                    <span class="meal-desc">${escapeHTML(mealsBySlot['Breakfast'])}</span>
                </div>
                <div class="meal-block">
                    <span class="meal-type"><i class="fas fa-sandwich"></i> Lunch</span>
                    <span class="meal-desc">${escapeHTML(mealsBySlot['Lunch'])}</span>
                </div>
                <div class="meal-block">
                    <span class="meal-type"><i class="fas fa-utensils"></i> Dinner</span>
                    <span class="meal-desc">${escapeHTML(mealsBySlot['Dinner'])}</span>
                </div>
            </div>
        `;
    }

    function renderChores(chores) {
        if (!el.choresList) return;
        if (el.choresCount) el.choresCount.textContent = `${chores.length} pending`;

        if (chores.length === 0) {
            el.choresList.innerHTML = '<div class="empty-state"><i class="fas fa-circle-check" style="margin-right:8px"></i> All chores completed!</div>';
            return;
        }

        el.choresList.innerHTML = chores.slice(0, 6).map(c => {
            const pClass = c.priority === 'high' ? 'p-high' : (c.priority === 'low' ? 'p-low' : 'p-medium');
            const assignee = c.assigned_to_name ? `<span class="chore-assigned">${escapeHTML(c.assigned_to_name)}</span>` : '';
            const points = c.points ? `<span class="chore-points">+${c.points} pts</span>` : '';

            return `
                <div class="chore-item">
                    <div class="chore-main">
                        <span class="chore-priority-dot ${pClass}"></span>
                        <span class="chore-title">${escapeHTML(c.title)}</span>
                    </div>
                    <div class="chore-meta">
                        ${assignee}
                        ${points}
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderGrocery(items) {
        if (!el.groceryList) return;
        const activeCount = items.filter(i => i.status === 'active').length;
        if (el.groceryCount) el.groceryCount.textContent = `${activeCount} to buy`;

        if (items.length === 0) {
            el.groceryList.innerHTML = '<div class="empty-state"><i class="fas fa-basket-shopping" style="margin-right:8px"></i> Grocery list is clear</div>';
            return;
        }

        el.groceryList.innerHTML = `
            <div class="grocery-tags">
                ${items.slice(0, 8).map(item => `
                    <div class="grocery-chip ${item.status === 'collected' ? 'collected' : ''}">
                        <i class="fas fa-${item.status === 'collected' ? 'check' : 'circle-plus'} text-muted"></i>
                        <span>${escapeHTML(item.name)}${item.quantity ? ` (${escapeHTML(item.quantity)})` : ''}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    function renderNotes(notes, messages) {
        if (!el.notesList) return;
        const count = notes.length + messages.length;
        if (el.notesCount) el.notesCount.textContent = `${count} notes`;

        if (notes.length === 0 && messages.length === 0) {
            el.notesList.innerHTML = '<div class="empty-state"><i class="fas fa-message" style="margin-right:8px"></i> No active notes or messages</div>';
            return;
        }

        const items = [];
        notes.slice(0, 2).forEach(n => {
            items.push(`
                <div class="tv-note">
                    <span class="tv-note-title"><i class="fas fa-thumbtack"></i> ${escapeHTML(n.title || 'Note')}</span>
                    <span class="tv-note-body">${escapeHTML(n.content || '')}</span>
                </div>
            `);
        });

        messages.slice(0, 2).forEach(m => {
            items.push(`
                <div class="tv-note" style="background:rgba(99, 102, 241, 0.08); border-color:rgba(99, 102, 241, 0.2)">
                    <span class="tv-note-title" style="color:var(--accent-light)"><i class="fas fa-comment"></i> ${escapeHTML(m.sender_name)}</span>
                    <span class="tv-note-body">${escapeHTML(m.content)}</span>
                </div>
            `);
        });

        el.notesList.innerHTML = `<div class="notes-container">${items.join('')}</div>`;
    }

    function renderPetCare(logs) {
        if (!el.petcareList) return;

        if (logs.length === 0) {
            el.petcareList.innerHTML = '<div class="empty-state">No recent pet updates logged</div>';
            return;
        }

        const latest = logs[0];
        let timeStr = 'Recently';
        try {
            timeStr = new Date(latest.timestamp).toLocaleTimeString('en-AU', { hour: '2-digit', minute: '2-digit' });
        } catch (e) {}

        el.petcareList.innerHTML = `
            <div class="petcare-row">
                <div>
                    <strong>${escapeHTML(latest.pet_name)}:</strong> ${escapeHTML(latest.action)}
                </div>
                <div class="petcare-meta">
                    ${latest.logged_by_name ? `by ${escapeHTML(latest.logged_by_name)} • ` : ''}${timeStr}
                </div>
            </div>
        `;
    }

    // =========================================================================
    // 4. Real-Time Server-Sent Events (SSE) & Fallback Polling
    // =========================================================================
    let eventSource = null;

    function initSSE() {
        if (!window.EventSource) {
            console.log('SSE not supported, running on periodic polling.');
            return;
        }

        try {
            if (eventSource) eventSource.close();
            eventSource = new EventSource('/api/tv/stream');

            eventSource.addEventListener('connected', () => {
                setOnlineStatus(true);
            });

            eventSource.addEventListener('update', (e) => {
                fetchSummary();
            });

            eventSource.addEventListener('ping', () => {
                setOnlineStatus(true);
            });

            eventSource.onerror = () => {
                // Connection lost; try reconnecting
                setOnlineStatus(false);
                eventSource.close();
                setTimeout(initSSE, 10000);
            };
        } catch (e) {
            console.warn('SSE initialization failed:', e);
            setTimeout(initSSE, 15000);
        }
    }

    function setOnlineStatus(online) {
        if (state.isOnline === online) return;
        state.isOnline = online;

        if (el.connStatus) {
            el.connStatus.className = `conn-badge ${online ? 'online' : 'offline'}`;
            el.connStatus.innerHTML = `<i class="fas fa-${online ? 'wifi' : 'wifi-slash'}"></i> ${online ? 'Connected' : 'Offline'}`;
        }

        if (el.toastOffline) {
            if (online) {
                el.toastOffline.classList.add('hidden');
            } else {
                el.toastOffline.classList.remove('hidden');
            }
        }
    }

    // =========================================================================
    // 5. Screen Protection & Screensaver
    // =========================================================================
    function resetInactivityTimer() {
        if (state.screensaverActive) {
            deactivateScreensaver();
        }

        clearTimeout(state.inactivityTimer);
        state.inactivityTimer = setTimeout(activateScreensaver, state.screensaverTimeout);
    }

    function activateScreensaver() {
        state.screensaverActive = true;
        if (el.screensaverOverlay) {
            el.screensaverOverlay.classList.remove('hidden');
        }
        updateClock();
    }

    function deactivateScreensaver() {
        state.screensaverActive = false;
        if (el.screensaverOverlay) {
            el.screensaverOverlay.classList.add('hidden');
        }
    }

    function setupScreenProtectionListeners() {
        ['mousemove', 'mousedown', 'keydown', 'touchstart'].forEach(evt => {
            window.addEventListener(evt, resetInactivityTimer, { passive: true });
        });
        resetInactivityTimer();
    }

    // Helper: HTML sanitization
    function escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // =========================================================================
    // 6. Bootstrap & Timers
    // =========================================================================
    function init() {
        // Run clock immediately and every 1s
        updateClock();
        setInterval(updateClock, 1000);

        // Initial Data Fetch
        fetchWeather();
        fetchSummary();

        // Polling Intervals:
        // Summary data polled every 20s as reliable heartbeat (plus SSE instant updates)
        setInterval(fetchSummary, 20000);

        // Weather polled every 15 minutes (Open-Meteo cache-friendly)
        setInterval(fetchWeather, 15 * 60 * 1000);

        // Initialize real-time stream
        initSSE();

        // Setup screen burn-in protection listeners
        setupScreenProtectionListeners();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
