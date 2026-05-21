-- NestBoard Database Schema

CREATE TABLE IF NOT EXISTS families (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    invite_code TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER REFERENCES families(id),
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'parent', 'child', 'guest')),
    first_name TEXT,
    last_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER REFERENCES families(id),
    title TEXT NOT NULL,
    description TEXT,
    assigned_to_id INTEGER REFERENCES users(id),
    points INTEGER DEFAULT 0,
    due_date TEXT,
    priority TEXT CHECK (priority IN ('low', 'medium', 'high')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'approved')),
    recurrence TEXT,
    created_by_id INTEGER REFERENCES users(id),
    approved_by_id INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER REFERENCES families(id),
    title TEXT NOT NULL,
    description TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    location TEXT,
    color TEXT,
    category TEXT,
    assigned_to_id INTEGER REFERENCES users(id),
    created_by_id INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER REFERENCES families(id),
    sender_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    attachment_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS grocery_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER REFERENCES families(id),
    name TEXT NOT NULL,
    quantity TEXT,
    category TEXT,
    added_by_id INTEGER REFERENCES users(id),
    edited_by_id INTEGER REFERENCES users(id),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'collected', 'purchased', 'archived')),
    collected_by_id INTEGER REFERENCES users(id),
    purchased_by_id INTEGER REFERENCES users(id),
    collected_at TIMESTAMP,
    purchased_at TIMESTAMP,
    deleted_at TIMESTAMP,
    is_pantry INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS grocery_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grocery_item_id INTEGER REFERENCES grocery_items(id),
    action TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    title TEXT NOT NULL,
    message TEXT,
    type TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER REFERENCES families(id),
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    category TEXT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER REFERENCES families(id),
    title TEXT,
    image_url TEXT NOT NULL,
    uploaded_by INTEGER REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending' CHECK (status IN ('approved', 'pending'))
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER REFERENCES families(id),
    title TEXT,
    content TEXT,
    color TEXT,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pet_care (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER REFERENCES families(id),
    pet_name TEXT NOT NULL,
    pet_type TEXT,
    action TEXT NOT NULL,
    status TEXT,
    logged_by_id INTEGER REFERENCES users(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS emergency_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER REFERENCES families(id),
    name TEXT NOT NULL,
    relationship TEXT,
    phone TEXT,
    email TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INTEGER REFERENCES families(id),
    day_of_week TEXT NOT NULL, -- 'Monday', 'Tuesday', etc.
    meal_type TEXT NOT NULL, -- 'Breakfast', 'Lunch', 'Dinner'
    description TEXT,
    recipe_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
