#!/usr/bin/env python3
"""
Startup script to run both FastAPI and Discord bot together.
Use this for systemd services or manual startup.
"""
import subprocess
import sys
import os
import signal
import time

def signal_handler(sig, frame):
    """Handle shutdown signals."""
    print("\nShutting down services...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Start both services."""
    print("=" * 60)
    print("Starting League Discord Bot Services")
    print("=" * 60)
    
    # Get port from environment or default
    port = os.getenv("PORT", "8000")
    api_host = os.getenv("API_HOST", "0.0.0.0")
    
    # Start FastAPI
    print(f"\n[1/2] Starting FastAPI server on {api_host}:{port}...")
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", 
         "--host", api_host, "--port", port],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # Wait a moment for API to start
    print("Waiting for API to initialize...")
    time.sleep(5)
    
    # Start Discord bot
    print(f"\n[2/2] Starting Discord bot...")
    bot_process = subprocess.Popen(
        [sys.executable, "bot/main.py"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    print("\n✅ Both services started!")
    print("Press Ctrl+C to stop both services\n")
    
    try:
        # Wait for both processes
        api_process.wait()
        bot_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        api_process.terminate()
        bot_process.terminate()
        api_process.wait()
        bot_process.wait()
        print("Services stopped.")

if __name__ == "__main__":
    main()

