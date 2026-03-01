#!/usr/bin/env python3
"""
Development server launcher with proper environment setup.
"""
import os
import sys

# Set environment variables BEFORE importing any modules
os.environ.setdefault('SQLITE_PATH', 'data/translateflow.db')
os.environ.setdefault('USE_SQLITE', 'true')

# Now import and run uvicorn
import uvicorn

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    print(f"[Launch] SQLITE_PATH={os.environ['SQLITE_PATH']}")
    print(f"[Launch] USE_SQLITE={os.environ['USE_SQLITE']}")

    uvicorn.run(
        "Tools.WebServer.web_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
