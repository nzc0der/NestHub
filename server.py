import os
import sys

# Ensure project root is on the path for relative imports.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting NestBoard server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
