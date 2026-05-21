import { chores, calendar } from '../api.js';

export async function render(container) {
    container.innerHTML = `
        <div class="dashboard-view">
            <header class="view-header">
                <h1>Family Overview</h1>
                <p>Welcome home!</p>
            </header>

            <div class="bento-grid">
                <div class="card grid-span-8">
                    <h3>Upcoming Events</h3>
                    <div id="dashboard-calendar"></div>
                </div>
                <div class="card grid-span-4">
                    <h3>Recent Chores</h3>
                    <div id="dashboard-chores"></div>
                </div>
            </div>
        </div>
    `;

    // Load some data
    try {
        const [choresList, eventsList] = await Promise.all([chores.list(), calendar.list()]);

        const choresDiv = document.getElementById('dashboard-chores');
        choresDiv.innerHTML = choresList.slice(0, 5).map(c => `
            <div class="item">
                <span>${c.title}</span>
                <span class="badge ${c.status}">${c.status}</span>
            </div>
        `).join('') || '<p>No active chores</p>';

        const eventsDiv = document.getElementById('dashboard-calendar');
        eventsDiv.innerHTML = eventsList.slice(0, 3).map(e => `
            <div class="item">
                <strong>${e.title}</strong> - ${new Date(e.start_time).toLocaleDateString()}
            </div>
        `).join('') || '<p>No upcoming events</p>';

    } catch (e) {
        console.error(e);
    }
}
