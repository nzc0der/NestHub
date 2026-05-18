#!/usr/bin/env python3
"""
auto_setup.py - Non-interactive automatic setup script.

Designed specifically for Noah's family setup.
If system config is missing, this script automatically creates config.json
and initialises the database schema. Then, it adds the default family users
if no users currently exist in the system, bypassing the interactive wizard.
"""

import os
import sys
import logging

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def main():
    print("=" * 60)
    print("  Family Dashboard - Automatic Setup Script")
    print("=" * 60)

    # 1. Initialize config.json if not present
    if not settings.is_initialized():
        print("[*] Config not initialized. Setting up defaults...")
        data_dir_default = os.path.join(PROJECT_ROOT, "data")
        backup_dir_default = os.path.join(PROJECT_ROOT, "backups")
        db_path = os.path.join(data_dir_default, "family.db")

        os.makedirs(data_dir_default, exist_ok=True)
        os.makedirs(backup_dir_default, exist_ok=True)

        config_data = {
            "db_path": db_path,
            "backup_dir": backup_dir_default,
            "secret_key": os.urandom(32).hex(),
            "project_root": PROJECT_ROOT,
        }
        settings.save_config(config_data)
        print(f"[+] config.json created successfully.")
    else:
        print("[~] config.json already exists.")

    # 2. Ensure schema is initialized
    print("[*] Verifying / Initializing database schema...")
    settings.init_schema()
    print("[+] Database schema verified.")

    # 3. Check for existing users
    try:
        existing_users = settings.get_users()
    except Exception as e:
        logger.error("Failed to retrieve users: %s", e)
        sys.exit(1)

    # Filter out guest to see if we have real users
    non_guest_users = [u for u in existing_users if u["username"] != "guest"]

    if len(non_guest_users) > 0:
        print("\n[!] Existing users found in database:")
        for u in non_guest_users:
            print(f"    - {u['username']} ({u['role']}, shopping: {u['shopping_permission']})")
        print("\n[~] Users already exist. Skipping automatic user creation.")
        print("=" * 60)
        sys.exit(0)

    # 4. Auto-add the family members
    # All users are created with NO PASSWORD (password=None).
    # When they first select their name on the login page, they are logged in password-free
    # and immediately prompted to configure a new password.
    family_members = [
        {"username": "noah", "role": "admin", "shopping_permission": "full"},
        {"username": "gaby", "role": "user", "shopping_permission": "full"},
        {"username": "ilan", "role": "user", "shopping_permission": "full"},
        {"username": "ari", "role": "user", "shopping_permission": "add"},  # Only Add not remove
    ]

    print("\n[*] Populating default family users...")
    for member in family_members:
        username = member["username"]
        role = member["role"]
        shopping_perm = member["shopping_permission"]
        try:
            settings.add_user(
                username=username,
                password=None,
                role=role,
                shopping_permission=shopping_perm
            )
            print(f"    [+] Created user '{username}' ({role}, shopping: {shopping_perm})")
        except Exception as e:
            logger.error("Failed to add user '%s': %s", username, e)
            sys.exit(1)

    # 5. Create guest user
    try:
        settings.add_user("guest", password=None, role="guest")
        print("    [+] Created user 'guest' (guest, no password)")
    except ValueError:
        print("    [~] Guest account already exists.")
    except Exception as e:
        logger.error("Failed to create guest user: %s", e)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  Automatic Setup Complete!")
    print("=" * 60)
    print(f"  Database Path   : {settings._db_path()}")
    print(f"  Backup Directory: {settings._backup_dir()}")
    print(f"  Initial Password: None (Users will be prompted to set a password on first login!)")
    print("=" * 60)

if __name__ == "__main__":
    main()
