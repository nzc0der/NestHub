import { auth } from './api.js';

export async function initAuth() {
    try {
        const { user } = await auth.me();
        updateUserUI(user);
        return user;
    } catch (e) {
        showAuthOverlay();
        return null;
    }
}

export function updateUserUI(user) {
    window.currentUser = user;
    document.getElementById('current-user-name').textContent = user.username;
    document.getElementById('current-user-role').textContent = user.role;
    document.getElementById('current-user-avatar').textContent = user.username[0].toUpperCase();

    if (user.role === 'admin') {
        document.querySelectorAll('.admin-only').forEach(el => el.classList.remove('hidden'));
    } else {
        document.querySelectorAll('.admin-only').forEach(el => el.classList.add('hidden'));
    }

    document.getElementById('auth-overlay').classList.add('hidden');
}

function showAuthOverlay() {
    document.getElementById('auth-overlay').classList.remove('hidden');
    initAuthTabs();
}

function initAuthTabs() {
    const tabs = document.querySelectorAll('.auth-tab');
    const container = document.querySelector('.auth-form-container');

    tabs.forEach(tab => {
        tab.onclick = () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            renderAuthForm(tab.dataset.tab, container);
        };
    });

    renderAuthForm('login', container);
}

function renderAuthForm(type, container) {
    if (type === 'login') {
        container.innerHTML = `
            <form id="login-form" class="auth-form">
                <h2>Welcome Back</h2>
                <div class="input-group">
                    <label>Username</label>
                    <input type="text" name="username" required>
                </div>
                <div class="input-group">
                    <label>Password</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit" class="btn btn-primary full-width">Login</button>
            </form>
        `;
        document.getElementById('login-form').onsubmit = handleLogin;
    } else if (type === 'signup') {
        container.innerHTML = `
            <form id="signup-form" class="auth-form">
                <h2>Start Your Nest</h2>
                <div class="input-group">
                    <label>Family Name</label>
                    <input type="text" name="family_name" required placeholder="The Smiths">
                </div>
                <div class="input-group">
                    <label>Admin Username</label>
                    <input type="text" name="username" required>
                </div>
                <div class="input-group">
                    <label>Password</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit" class="btn btn-primary full-width">Create Family</button>
            </form>
        `;
        document.getElementById('signup-form').onsubmit = handleSignup;
    } else if (type === 'join') {
        container.innerHTML = `
            <form id="join-form" class="auth-form">
                <h2>Join Your Family</h2>
                <div class="input-group">
                    <label>Invite Code</label>
                    <input type="text" name="invite_code" required placeholder="ABC12345">
                </div>
                <div class="input-group">
                    <label>Username</label>
                    <input type="text" name="username" required>
                </div>
                <div class="input-group">
                    <label>Password</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit" class="btn btn-primary full-width">Join</button>
            </form>
        `;
        document.getElementById('join-form').onsubmit = handleJoin;
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    try {
        const { user } = await auth.login(data);
        updateUserUI(user);
        window.location.reload();
    } catch (err) { alert(err.message); }
}

async function handleSignup(e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    try {
        const res = await auth.signup(data);
        alert(`Family created! Your invite code is: ${res.invite_code}`);
        const { user } = await auth.login({username: data.username, password: data.password});
        updateUserUI(user);
        window.location.reload();
    } catch (err) { alert(err.message); }
}

async function handleJoin(e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    try {
        await auth.join(data);
        const { user } = await auth.login({username: data.username, password: data.password});
        updateUserUI(user);
        window.location.reload();
    } catch (err) { alert(err.message); }
}
