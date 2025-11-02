#!/usr/bin/env python3
"""
E-Voting System - Automated Startup Script
Starts all three services simultaneously
"""

import subprocess
import sys
import time
import os
import signal

def print_banner():
    print("=" * 70)
    print(" " * 15 + "E-VOTING SYSTEM LAUNCHER")
    print("=" * 70)
    print()

def check_dependencies():
    """Check if required packages are installed"""
    required = ['flask', 'cryptography', 'requests', 'matplotlib']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("⚠️  Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstalling missing packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("✅ All packages installed!\n")

def start_all_services():
    """Start all three services in separate subprocesses"""
    services = [
        ("encryption_service.py", "Encryption Service", 5001),
        ("storage_service.py", "Storage Service", 5002),
        ("app.py", "Main Application", 5000)
    ]
    
    processes = []
    
    for script, name, port in services:
        if not os.path.exists(script):
            print(f"❌ ERROR: {script} not found in current directory!")
            return None
        
        try:
            print(f"🚀 Starting {name} on port {port}...")
            
            # Start process without capturing output (let it print to console)
            process = subprocess.Popen(
                [sys.executable, script],
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            
            processes.append({
                'process': process,
                'name': name,
                'port': port
            })
            
            time.sleep(2)  # Wait 2 seconds between starting each service
            
        except Exception as e:
            print(f"❌ Error starting {name}: {e}")
            return None
    
    return processes

def cleanup_processes(processes):
    """Terminate all running processes"""
    if processes:
        print("\n🛑 Stopping all services...")
        for service in processes:
            try:
                service['process'].terminate()
                print(f"   ✓ Stopped {service['name']}")
            except:
                pass

def main():
    print_banner()
    
    # Check dependencies
    print("📦 Checking dependencies...")
    try:
        check_dependencies()
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        print("Please install manually: pip install flask cryptography requests matplotlib")
        return
    
    print("\n" + "=" * 70)
    print("Starting E-Voting System Services...")
    print("=" * 70 + "\n")
    
    # Start all services
    processes = start_all_services()
    
    if not processes:
        print("❌ Failed to start services")
        return
    
    # Wait a bit for services to initialize
    print("\n⏳ Waiting for services to initialize...")
    time.sleep(3)
    
    print("\n" + "=" * 70)
    print("✅ E-VOTING SYSTEM IS NOW RUNNING!")
    print("=" * 70)
    print("\n📍 Access Points:")
    print("   🌐 Main Application:  http://127.0.0.1:5000")
    print("   🔐 Admin Panel:       http://127.0.0.1:5000/admin")
    print("   🔒 Encryption API:    http://127.0.0.1:5001")
    print("   💾 Storage API:       http://127.0.0.1:5002")
    print("\n⚠️  Press Ctrl+C to stop all services")
    print("=" * 70 + "\n")
    
    try:
        # Keep the main thread alive and monitor processes
        while True:
            # Check if any process has died
            for service in processes:
                if service['process'].poll() is not None:
                    print(f"⚠️  {service['name']} has stopped unexpectedly!")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down E-Voting System...")
        print("=" * 70)
        cleanup_processes(processes)
        print("✅ All services stopped")
        print("=" * 70)
        sys.exit(0)

if __name__ == "__main__":
    main()