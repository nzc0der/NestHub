import { extra } from '../api.js';

export async function render(container) {
    container.innerHTML = `
        <div class="extras-view">
            <header class="view-header">
                <h1>Family Extras</h1>
            </header>
            <div class="bento-grid">
                <div class="card grid-span-6">
                    <h3>Photo Gallery</h3>
                    <div id="photo-gallery" class="gallery-grid"></div>
                    <button class="btn btn-ghost full-width mt-10">Upload Photo</button>
                </div>
                <div class="card grid-span-6">
                    <h3>Sticky Notes</h3>
                    <div id="sticky-notes" class="notes-grid"></div>
                    <button class="btn btn-ghost full-width mt-10">Add Note</button>
                </div>
                <div class="card grid-span-6">
                    <h3>Pet Care Log</h3>
                    <div id="pet-log"></div>
                </div>
                <div class="card grid-span-6">
                    <h3>Emergency Contacts</h3>
                    <div id="emergency-contacts"></div>
                </div>
            </div>
        </div>
    `;

    // Photos
    const photos = await extra.getPhotos();
    document.getElementById('photo-gallery').innerHTML = photos.map(p => `
        <div class="photo-item ${p.status}">
            <img src="${p.image_url}" alt="${p.title || 'Family Photo'}">
            ${p.status === 'pending' ? '<span class="status-badge">Pending Approval</span>' : ''}
        </div>
    `).join('') || '<p>No photos yet</p>';

    // Notes
    const notes = await extra.getNotes();
    document.getElementById('sticky-notes').innerHTML = notes.map(n => `
        <div class="note-item" style="background-color: ${n.color || '#fef08a'}">
            <h4>${n.title || ''}</h4>
            <p>${n.content || ''}</p>
        </div>
    `).join('') || '<p>No notes yet</p>';

    // Pet Care
    const petCare = await extra.getPetCare();
    document.getElementById('pet-log').innerHTML = petCare.map(l => `
        <div class="log-entry">
            <strong>${l.pet_name}:</strong> ${l.action} (${new Date(l.timestamp).toLocaleTimeString()})
        </div>
    `).join('') || '<p>No pet care logs</p>';

    // Emergency Contacts
    const contacts = await extra.getEmergency();
    document.getElementById('emergency-contacts').innerHTML = contacts.map(c => `
        <div class="contact-item">
            <strong>${c.name}</strong> (${c.relationship})<br>
            <a href="tel:${c.phone}">${c.phone}</a>
        </div>
    `).join('') || '<p>No contacts yet</p>';
}
