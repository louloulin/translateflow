#!/usr/bin/env python3
"""Script to run the TranslateFlow web server standalone."""

import sys
sys.path.insert(0, '/Users/louloulin/Documents/linchong/ai/AiNiee-Next')

from Tools.WebServer.web_server import run_server
import time

if __name__ == "__main__":
    print("Starting TranslateFlow Web Server on http://localhost:8000")
    thread = run_server(host="127.0.0.1", port=8000, monitor_mode=False)
    
    if thread:
        print("Server started successfully!")
        print("Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
    else:
        print("Failed to start server")
        sys.exit(1)
