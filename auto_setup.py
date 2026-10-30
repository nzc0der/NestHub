#!/usr/bin/env python3
"""
Netlify build setup script for NestHub frontend.
Validates frontend assets before Netlify static publishing.
"""
import sys
import os

def main():
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    if not os.path.isdir(frontend_dir):
        print(f"Error: Frontend directory not found at {frontend_dir}", file=sys.stderr)
        sys.exit(1)

    index_html = os.path.join(frontend_dir, "index.html")
    if not os.path.isfile(index_html):
        print(f"Error: index.html not found in {frontend_dir}", file=sys.stderr)
        sys.exit(1)

    print("Netlify build setup: Frontend assets verified successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
