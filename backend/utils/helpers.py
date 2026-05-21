import bcrypt
import uuid

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_invite_code():
    return str(uuid.uuid4())[:8].upper()

def sanitize_input(text):
    if text is None:
        return ""
    return text.strip()
