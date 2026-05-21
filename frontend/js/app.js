import { initAuth } from './auth.js';

const routes = {
    '/': 'dashboard',
    '/calendar': 'calendar',
    '/chores': 'chores',
    '/grocery': 'grocery',
    '/meals': 'meals',
    '/messages': 'messages',
    '/extras': 'extras',
    '/admin': 'admin'
};

async function router() {
    const path = window.location.pathname;
    const view = routes[path] || 'dashboard';

    document.querySelectorAll('.nav-item, .mobile-nav-item').forEach(el => {
        el.classList.toggle('active', el.getAttribute('data-view') === view);
    });

    const container = document.getElementById('view-container');
    container.innerHTML = '<div class="loader"></div>';

    try {
        const module = await import(`./views/${view}.js`);
        container.innerHTML = '';
        module.render(container);
    } catch (e) {
        console.error('Failed to load view:', e);
        container.innerHTML = `<h1>404 Not Found</h1><p>The view ${view} could not be loaded.</p>`;
    }
}

// Modal helper
export function showFormModal(title, fields, onSubmit) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal-card glass">
            <h2>${title}</h2>
            <form id="modal-form">
                ${fields.map(f => `
                    <div class="input-group">
                        <label>${f.label}</label>
                        <input type="${f.type || 'text'}" name="${f.name}" ${f.required ? 'required' : ''} value="${f.value || ''}">
                    </div>
                `).join('')}
                <div class="modal-actions">
                    <button type="button" class="btn btn-ghost" id="modal-cancel">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save</button>
                </div>
            </form>
        </div>
    `;
    document.body.appendChild(overlay);

    document.getElementById('modal-cancel').onclick = () => overlay.remove();
    document.getElementById('modal-form').onsubmit = (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target));
        onSubmit(data);
        overlay.remove();
    };
}

window.addEventListener('click', e => {
    const link = e.target.closest('a');
    if (link && link.href && link.href.startsWith(window.location.origin) && !link.target) {
        e.preventDefault();
        window.history.pushState(null, null, link.href);
        router();
    }
});

window.addEventListener('popstate', router);

document.addEventListener('DOMContentLoaded', () => {
    initAuth().then(user => {
        if (user) router();
    });
});
