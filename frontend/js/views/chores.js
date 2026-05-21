import { chores } from '../api.js';
import { showFormModal } from '../app.js';

export async function render(container) {
    container.innerHTML = `
        <div class="chores-view">
            <header class="view-header">
                <h1>Chore Tracker</h1>
                <button class="btn btn-primary" id="add-chore-btn">Add Chore</button>
            </header>
            <div class="chores-list" id="chores-container"></div>
        </div>
    `;

    const loadChores = async () => {
        const list = await chores.list();
        const containerDiv = document.getElementById('chores-container');
        containerDiv.innerHTML = list.map(c => `
            <div class="card chore-card ${c.status}">
                <div class="chore-info">
                    <h3>${c.title}</h3>
                    <p>${c.description || ''}</p>
                    <div class="meta">
                        <span class="priority">${c.priority}</span>
                        <span class="points">${c.points} XP</span>
                        <span class="badge ${c.status}">${c.status}</span>
                    </div>
                </div>
                <div class="chore-actions">
                    ${c.status === 'pending' || c.status === 'in_progress' ?
                        `<button class="btn btn-ghost action-btn" data-id="${c.id}" data-status="completed">Complete</button>` : ''}
                    ${(c.status === 'completed') && (window.currentUser.role === 'admin' || window.currentUser.role === 'parent') ?
                        `<button class="btn btn-primary action-btn" data-id="${c.id}" data-status="approved">Approve</button>` : ''}
                </div>
            </div>
        `).join('') || '<p>All done! No chores left.</p>';

        containerDiv.querySelectorAll('.action-btn').forEach(btn => {
            btn.onclick = async () => {
                await chores.updateStatus(btn.dataset.id, btn.dataset.status);
                loadChores();
            };
        });
    };

    document.getElementById('add-chore-btn').onclick = () => {
        showFormModal('Add New Chore', [
            { name: 'title', label: 'Chore Title', required: true },
            { name: 'description', label: 'Description' },
            { name: 'points', label: 'XP Points', type: 'number', value: 10 }
        ], async (data) => {
            await chores.create(data);
            loadChores();
        });
    };

    await loadChores();
}
