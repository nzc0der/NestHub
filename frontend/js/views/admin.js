import { admin } from '../api.js';

export async function render(container) {
    container.innerHTML = `
        <div class="admin-view">
            <header class="view-header">
                <h1>Administration</h1>
                <p>Manage family members and monitor system health</p>
            </header>
            <div class="bento-grid">
                <div class="card grid-span-12">
                    <h3 class="mb-20">Family Statistics</h3>
                    <div id="admin-stats" class="stats-row" style="display: flex; gap: 40px;">
                        <div class="loader"></div>
                    </div>
                </div>

                <div class="card grid-span-8">
                    <h3 class="mb-20">Family Members</h3>
                    <div id="admin-users"></div>
                </div>

                <div class="card grid-span-4">
                    <h3 class="mb-20">System Health</h3>
                    <div id="admin-diagnostics">
                        <div class="loader"></div>
                    </div>
                </div>

                <div class="card grid-span-12">
                    <h3 class="mb-20">Recent Activity Logs</h3>
                    <div id="admin-logs"></div>
                </div>
            </div>
        </div>
    `;

    try {
        const [stats, users, logs, diag] = await Promise.all([
            admin.getStats(),
            admin.getUsers(),
            admin.getLogs(),
            admin.getDiagnostics()
        ]);

        document.getElementById('admin-stats').innerHTML = `
            <div class="stat-card">
                <div class="stat-label">Total Members</div>
                <div class="stat-value">${stats.user_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Active Chores</div>
                <div class="stat-value">${stats.chore_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Items Needed</div>
                <div class="stat-value">${stats.grocery_count}</div>
            </div>
        `;

        document.getElementById('admin-users').innerHTML = `
            <table class="admin-table" style="width: 100%; border-collapse: collapse;">
                <thead style="text-align: left; color: var(--text-muted); font-size: 12px; text-transform: uppercase;">
                    <tr><th style="padding: 12px;">User</th><th>Role</th><th>Actions</th></tr>
                </thead>
                <tbody>
                    ${users.map(u => `
                        <tr style="border-top: 1px solid var(--border);">
                            <td style="padding: 16px; font-weight: 700;">${u.username}</td>
                            <td><span class="badge ${u.role}">${u.role}</span></td>
                            <td><button class="btn-sm btn-ghost">Edit</button></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        document.getElementById('admin-diagnostics').innerHTML = `
            <div class="diag-list" style="display: flex; flex-direction: column; gap: 12px;">
                <div class="diag-item"><span>CPU Usage:</span> <strong>${diag.cpu_usage}</strong></div>
                <div class="diag-item"><span>Memory:</span> <strong>${diag.memory_used}</strong> (${diag.memory_total})</div>
                <div class="diag-item"><span>Disk Free:</span> <strong>${diag.disk_free}</strong></div>
                <div class="diag-item"><span>OS:</span> <strong>${diag.os}</strong></div>
                <div class="diag-item"><span>Python:</span> <strong>${diag.python_version}</strong></div>
            </div>
        `;

        document.getElementById('admin-logs').innerHTML = logs.slice(0, 15).map(l => `
            <div class="log-item" style="padding: 12px; border-bottom: 1px solid var(--border); font-size: 13px; display: flex; gap: 20px;">
                <span style="color: var(--text-dim); white-space: nowrap;">${new Date(l.timestamp).toLocaleString()}</span>
                <span style="font-weight: 700; color: var(--primary); min-width: 100px;">${l.action.toUpperCase()}</span>
                <span style="color: var(--text-muted);">${l.details || ''}</span>
            </div>
        `).join('') || '<p>No logs yet</p>';

    } catch (e) {
        console.error(e);
        container.innerHTML += `<p class="error">Access Denied or Error: ${e.message}</p>`;
    }
}
