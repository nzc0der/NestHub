import { grocery } from '../api.js';
import { showFormModal } from '../app.js';

export async function render(container) {
    container.innerHTML = `
        <div class="grocery-view">
            <header class="view-header">
                <h1>Family Grocery List</h1>
                <button class="btn btn-primary" id="add-item-btn">Add Item</button>
            </header>
            <div class="grocery-container">
                <div class="card">
                    <div id="grocery-list"></div>
                </div>
            </div>
        </div>
    `;

    const loadItems = async () => {
        const list = await grocery.list();
        const listDiv = document.getElementById('grocery-list');
        const isParentOrAdmin = window.currentUser.role === 'admin' || window.currentUser.role === 'parent';

        listDiv.innerHTML = list.map(item => `
            <div class="grocery-item ${item.status}">
                <div class="item-main">
                    <span class="name">${item.name}</span>
                    <span class="qty">${item.quantity || ''}</span>
                    <span class="badge ${item.status}">${item.status}</span>
                </div>
                <div class="item-actions">
                    ${item.status === 'active' ? `<button class="btn-sm collect-btn" data-id="${item.id}">Collect</button>` : ''}
                    ${(item.status === 'collected') && isParentOrAdmin ? `<button class="btn-sm purchase-btn" data-id="${item.id}">Purchase</button>` : ''}
                    ${isParentOrAdmin ? `<button class="btn-sm text-danger delete-btn" data-id="${item.id}"><i class="fas fa-trash"></i></button>` : ''}
                </div>
            </div>
        `).join('') || '<p>List is empty</p>';

        listDiv.querySelectorAll('.collect-btn').forEach(btn => {
            btn.onclick = async () => {
                await grocery.update(btn.dataset.id, { status: 'collected' });
                loadItems();
            };
        });

        listDiv.querySelectorAll('.purchase-btn').forEach(btn => {
            btn.onclick = async () => {
                await grocery.update(btn.dataset.id, { status: 'purchased' });
                loadItems();
            };
        });

        listDiv.querySelectorAll('.delete-btn').forEach(btn => {
            btn.onclick = async () => {
                if(confirm('Delete item?')) {
                    await grocery.delete(btn.dataset.id);
                    loadItems();
                }
            };
        });
    };

    document.getElementById('add-item-btn').onclick = () => {
        showFormModal('Add Grocery Item', [
            { name: 'name', label: 'Item Name', required: true },
            { name: 'quantity', label: 'Quantity (e.g. 2L, 1 pack)' },
            { name: 'category', label: 'Category' }
        ], async (data) => {
            await grocery.create(data);
            loadItems();
        });
    };

    await loadItems();
}
