import os, sys, settings, os.urandom
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path: sys.path.insert(0, PROJECT_ROOT)

def run_setup():
    if settings.is_initialized(): return
    cfg = {"db_path": os.path.join(PROJECT_ROOT, "data", "family.db"), "backup_dir": os.path.join(PROJECT_ROOT, "backups"), "port": 8000, "latitude": -37.9034, "longitude": 145.0416, "city": "Ormond", "secret_key": os.urandom(32).hex(), "project_root": PROJECT_ROOT}
    settings.save_config(cfg)
    settings.init_schema()
    settings.add_user("admin", "password123", "admin")
    settings.add_user("guest", None, "guest")

if __name__ == "__main__":
    run_setup()
