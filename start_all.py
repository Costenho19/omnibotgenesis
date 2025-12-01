#!/usr/bin/env python3
"""
OMNIX V6.5 - Process Supervisor
Runs both trading bot and dashboard, restarts on failure.
"""

import subprocess
import sys
import signal
import time
import os

processes = {}

def log(msg):
    print(f"[SUPERVISOR] {msg}", flush=True)

def start_process(name, command):
    """Start a process and track it."""
    log(f"Starting {name}: {command}")
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
        preexec_fn=os.setsid
    )
    processes[name] = proc
    return proc

def terminate_all():
    """Terminate all tracked processes."""
    for name, proc in processes.items():
        if proc.poll() is None:
            log(f"Terminating {name}...")
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    log(f"Received signal {signum}, shutting down...")
    terminate_all()
    sys.exit(0)

def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    log("OMNIX V6.5 Supervisor starting...")
    
    bot = start_process("Trading Bot", "python -u main.py")
    time.sleep(2)
    dashboard = start_process("Dashboard", "python start_dashboard.py")
    
    log("All processes started. Monitoring...")
    
    while True:
        for name, proc in list(processes.items()):
            exit_code = proc.poll()
            if exit_code is not None:
                log(f"{name} exited with code {exit_code}")
                terminate_all()
                sys.exit(exit_code if exit_code != 0 else 1)
        
        time.sleep(1)

if __name__ == "__main__":
    main()
