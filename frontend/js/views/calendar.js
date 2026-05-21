import { calendar } from '../api.js';
import { showFormModal } from '../app.js';

export async function render(container) {
    container.innerHTML = `
        <div class="calendar-view">
            <header class="view-header">
                <h1>Shared Calendar</h1>
                <button class="btn btn-primary" id="add-event-btn">Add Event</button>
            </header>
            <div class="card" id="calendar-container">
                <div id="events-list"></div>
            </div>
        </div>
    `;

    const loadEvents = async () => {
        const eventsList = await calendar.list();
        const listDiv = document.getElementById('events-list');
        listDiv.innerHTML = eventsList.map(e => `
            <div class="item">
                <div class="date">${new Date(e.start_time).toLocaleString()}</div>
                <div class="title"><strong>${e.title}</strong></div>
                <p>${e.description || ''}</p>
                <button class="btn-sm text-danger delete-btn" data-id="${e.id}">Delete</button>
            </div>
        `).join('') || '<p>No events found</p>';

        listDiv.querySelectorAll('.delete-btn').forEach(btn => {
            btn.onclick = async () => {
                if(confirm('Delete event?')) {
                    await calendar.delete(btn.dataset.id);
                    loadEvents();
                }
            };
        });
    };

    document.getElementById('add-event-btn').onclick = () => {
        showFormModal('Add Event', [
            { name: 'title', label: 'Event Title', required: true },
            { name: 'description', label: 'Description' },
            { name: 'start_time', label: 'Date & Time', type: 'datetime-local', required: true }
        ], async (data) => {
            await calendar.create(data);
            loadEvents();
        });
    };

    await loadEvents();
}
