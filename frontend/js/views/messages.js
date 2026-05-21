import { messages } from '../api.js';

export async function render(container) {
    container.innerHTML = `
        <div class="messages-view">
            <header class="view-header">
                <h1>Family Chat</h1>
            </header>
            <div class="chat-container card">
                <div id="chat-messages" class="chat-messages"></div>
                <form id="chat-form" class="chat-input">
                    <input type="text" id="msg-input" placeholder="Type a message..." required>
                    <button type="submit" class="btn btn-primary">Send</button>
                </form>
            </div>
        </div>
    `;

    const loadMessages = async () => {
        const list = await messages.list();
        const chatDiv = document.getElementById('chat-messages');
        const currentUserId = window.currentUser.id;

        chatDiv.innerHTML = list.map(m => `
            <div class="msg ${m.sender_id === currentUserId ? 'me' : 'other'}">
                <div class="sender">${m.sender_name}</div>
                <div class="content">${m.content}</div>
                <div class="time">${new Date(m.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
            </div>
        `).join('');
        chatDiv.scrollTop = chatDiv.scrollHeight;
    };

    await loadMessages();

    document.getElementById('chat-form').onsubmit = async (e) => {
        e.preventDefault();
        const input = document.getElementById('msg-input');
        await messages.send(input.value);
        input.value = '';
        await loadMessages();
    };
}
