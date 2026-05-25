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

    if (user.role === 'admin' || user.role === 'parent') {
        document.querySelectorAll('.admin-only').forEach(el => el.classList.remove('hidden'));
    } else {
        document.querySelectorAll('.admin-only').forEach(el => el.classList.add('hidden'));
    }

    document.getElementById('auth-overlay').classList.add('hidden');
}

function showAuthOverlay() {
    document.getElementById('auth-overlay').classList.remove('hidden');
    initAuthEventListeners();
}

function initAuthEventListeners() {
    const tabs = document.querySelectorAll('.auth-tab');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');

    tabs.forEach(tab => {
        tab.onclick = () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            if (tab.dataset.tab === 'login') {
                loginForm.classList.remove('hidden');
                signupForm.classList.add('hidden');
            } else {
                loginForm.classList.add('hidden');
                signupForm.classList.remove('hidden');
            }
        };
    });

    loginForm.onsubmit = handleLogin;
    signupForm.onsubmit = handleSignup;
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
        await auth.signup(data);
        const { user } = await auth.login({username: data.username, password: data.password});
        updateUserUI(user);
        window.location.reload();
    } catch (err) { alert(err.message); }
}
