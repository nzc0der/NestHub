const API_BASE = '/api';

async function request(url, options = {}) {
    const response = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    });

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || 'Something went wrong');
    }
    return data;
}

export const auth = {
    login: (credentials) => request('/auth/login', { method: 'POST', body: JSON.stringify(credentials) }),
    signup: (data) => request('/auth/signup', { method: 'POST', body: JSON.stringify(data) }),
    join: (data) => request('/auth/join', { method: 'POST', body: JSON.stringify(data) }),
    logout: () => request('/auth/logout', { method: 'POST' }),
    me: () => request('/auth/me'),
};

export const chores = {
    list: () => request('/chores/'),
    create: (data) => request('/chores/', { method: 'POST', body: JSON.stringify(data) }),
    updateStatus: (id, status) => request(`/chores/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) }),
    delete: (id) => request(`/chores/${id}`, { method: 'DELETE' }),
};

export const calendar = {
    list: () => request('/calendar/'),
    create: (data) => request('/calendar/', { method: 'POST', body: JSON.stringify(data) }),
    delete: (id) => request(`/calendar/${id}`, { method: 'DELETE' }),
};

export const grocery = {
    list: () => request('/grocery/'),
    create: (data) => request('/grocery/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) => request(`/grocery/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id) => request(`/grocery/${id}`, { method: 'DELETE' }),
};

export const meals = {
    list: () => request('/meals/'),
    create: (data) => request('/meals/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) => request(`/meals/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id) => request(`/meals/${id}`, { method: 'DELETE' }),
};

export const messages = {
    list: () => request('/messages/'),
    send: (content) => request('/messages/', { method: 'POST', body: JSON.stringify({ content }) }),
};

export const extra = {
    getPhotos: () => request('/extra/photos'),
    uploadPhoto: (data) => request('/extra/photos', { method: 'POST', body: JSON.stringify(data) }),
    approvePhoto: (id) => request(`/extra/photos/${id}/approve`, { method: 'PUT' }),
    getNotes: () => request('/extra/notes'),
    addNote: (data) => request('/extra/notes', { method: 'POST', body: JSON.stringify(data) }),
    updateNote: (id, data) => request(`/extra/notes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    getPetCare: () => request('/extra/pet_care'),
    logPetCare: (data) => request('/extra/pet_care', { method: 'POST', body: JSON.stringify(data) }),
    getEmergency: () => request('/extra/emergency_contacts'),
    addEmergency: (data) => request('/extra/emergency_contacts', { method: 'POST', body: JSON.stringify(data) }),
};

export const admin = {
    getUsers: () => request('/admin/users'),
    getLogs: () => request('/admin/logs'),
    getStats: () => request('/admin/stats'),
    getDiagnostics: () => request('/admin/diagnostics'),
    updateRole: (userId, role) => request(`/admin/users/${userId}/role`, { method: 'PUT', body: JSON.stringify({ role }) }),
};
