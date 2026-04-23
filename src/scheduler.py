"""
Scheduler for Daily Sales Briefing

Runs the briefing pipeline automatically at a scheduled time each day.

Usage:
  python3 scheduler.py

This script runs continuously and fires main.py at the configured time.
For production use on Windows, consider using Task Scheduler instead.
For production use on Linux/macOS, consider using cron instead.

Example cron entry (runs every day at 8:00 AM):
  0 8 * * * cd /path/to/morning_briefing && /usr/bin/python3 src/main.py

Example Windows Task Scheduler command:
  python C:\\path\\to\\morning_briefing\\src\\main.py
"""

import schedule
import time
import subprocess
import sys
import os
import configparser
from datetime import datetime


def run_briefing():
    """Execute the main briefing script."""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running briefing...")
    
    main_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
    result = subprocess.run(
        [sys.executable, main_script],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Briefing sent successfully.")
    else:
        print(f"✗ Briefing failed (exit code {result.returncode})")
        if result.stderr:
            print(f"  Error: {result.stderr[:200]}")
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Next run in 24 hours.")


def main():
    # Load schedule time from config
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, 'config', 'config.ini')
    
    if not os.path.exists(config_path):
        print(f"Config not found: {config_path}")
        print("Copy config.ini.example to config.ini and configure it first.")
        sys.exit(1)
    
    config = configparser.ConfigParser()
    config.read(config_path)
    
    run_time = config.get('schedule', 'daily_run_time', fallback='08:00')
    
    print("=" * 60)
    print("  Daily Sales Briefing — Scheduler")
    print("=" * 60)
    print(f"  Scheduled run time: {run_time} daily")
    print(f"  Current time:       {datetime.now().strftime('%H:%M:%S')}")
    print(f"  Press Ctrl+C to stop the scheduler")
    print("=" * 60)
    
    # Schedule the job
    schedule.every().day.at(run_time).do(run_briefing)
    
    # Keep running until interrupted
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        print("\n\nScheduler stopped.")
        sys.exit(0)


if __name__ == '__main__':
    main()
