#!/usr/bin/env python3
"""
E-Voting System Diagnostic Tool
Checks all services and identifies issues
"""

import requests
import os
import sys
import socket

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def check_port_available(port):
    """Check if a port is available or in use"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0  # True if port is in use (service is running)

def check_file_exists(filename):
    """Check if a required file exists"""
    exists = os.path.exists(filename)
    status = "✅ Found" if exists else "❌ Missing"
    print(f"   {filename}: {status}")
    return exists

def check_directory_exists(dirname):
    """Check if a required directory exists"""
    exists = os.path.exists(dirname)
    status = "✅ Found" if exists else "⚠️  Missing (will be created)"
    print(f"   {dirname}/: {status}")
    return exists

def test_service_health(url, service_name):
    """Test if a service is responding"""
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            print(f"   ✅ {service_name} is responding")
            print(f"      Status: {response.json()}")
            return True
        else:
            print(f"   ⚠️  {service_name} responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ {service_name} is not running or not accessible")
        return False
    except requests.exceptions.Timeout:
        print(f"   ⚠️  {service_name} timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_dependencies():
    """Check if required Python packages are installed"""
    packages = {
        'flask': 'Flask',
        'cryptography': 'Cryptography',
        'requests': 'Requests',
        'matplotlib': 'Matplotlib (for analysis module)'
    }
    
    missing = []
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - NOT INSTALLED")
            missing.append(module)
    
    return missing

def main():
    print_header("E-VOTING SYSTEM DIAGNOSTIC TOOL")
    
    # Check 1: Required Files
    print_header("1. Checking Required Files")
    files_ok = True
    files_ok &= check_file_exists("app.py")
    files_ok &= check_file_exists("encryption_service.py")
    files_ok &= check_file_exists("storage_service.py")
    
    if not files_ok:
        print("\n⚠️  WARNING: Some required files are missing!")
    
    # Check 2: Directories
    print_header("2. Checking Directories")
    check_directory_exists("data")
    check_directory_exists("keys")
    check_directory_exists("templates")
    check_directory_exists("outputs")
    
    # Check 3: Python Dependencies
    print_header("3. Checking Python Dependencies")
    missing = check_dependencies()
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"\nInstall with: pip install {' '.join(missing)}")
    
    # Check 4: Port Availability
    print_header("4. Checking Port Status")
    ports = {
        5000: "Main Application",
        5001: "Encryption Service",
        5002: "Storage Service"
    }
    
    running_services = []
    for port, name in ports.items():
        if check_port_available(port):
            print(f"   ✅ Port {port} ({name}) - IN USE (service running)")
            running_services.append(port)
        else:
            print(f"   ❌ Port {port} ({name}) - NOT IN USE (service not running)")
    
    # Check 5: Service Health Checks
    if running_services:
        print_header("5. Testing Service Health")
        
        if 5001 in running_services:
            test_service_health("http://127.0.0.1:5001/health", "Encryption Service")
        
        if 5002 in running_services:
            test_service_health("http://127.0.0.1:5002/health", "Storage Service")
        
        if 5000 in running_services:
            test_service_health("http://127.0.0.1:5000/", "Main Application")
    else:
        print_header("5. Service Health")
        print("   ⚠️  No services are currently running")
        print("   Run start_evoting.bat or start the services manually")
    
    # Check 6: API Endpoints Test
    if 5001 in running_services and 5002 in running_services:
        print_header("6. Testing API Endpoints")
        
        # Test encryption endpoint
        try:
            test_data = {
                "voter_id": "TEST123",
                "candidate": "A",
                "timestamp": "2025-10-30 12:00:00"
            }
            response = requests.post("http://127.0.0.1:5001/encrypt_vote", json=test_data, timeout=5)
            if response.status_code == 200:
                print("   ✅ Encryption endpoint working")
            else:
                print(f"   ❌ Encryption endpoint error: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Encryption endpoint failed: {e}")
        
        # Test storage endpoint
        try:
            response = requests.get("http://127.0.0.1:5002/ledger", timeout=5)
            if response.status_code == 200:
                print("   ✅ Storage ledger endpoint working")
                data = response.json()
                print(f"      Total votes in ledger: {data.get('metadata', {}).get('total_votes', 0)}")
            else:
                print(f"   ❌ Storage endpoint error: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Storage endpoint failed: {e}")
    
    # Summary
    print_header("DIAGNOSTIC SUMMARY")
    
    if not files_ok:
        print("❌ CRITICAL: Required Python files are missing")
        print("   Make sure all .py files are in the current directory")
    
    if missing:
        print(f"❌ CRITICAL: Missing Python packages: {', '.join(missing)}")
        print(f"   Install with: pip install {' '.join(missing)}")
    
    if len(running_services) == 0:
        print("❌ CRITICAL: No services are running")
        print("   Solution: Run start_evoting.bat or start services manually:")
        print("     Terminal 1: python encryption_service.py")
        print("     Terminal 2: python storage_service.py")
        print("     Terminal 3: python app.py")
    elif len(running_services) < 3:
        print(f"⚠️  WARNING: Only {len(running_services)}/3 services running")
        not_running = [ports[p] for p in [5000, 5001, 5002] if p not in running_services]
        print(f"   Not running: {', '.join(not_running)}")
    else:
        print("✅ ALL SYSTEMS OPERATIONAL")
        print("\n   Access Points:")
        print("   • Main App: http://127.0.0.1:5000")
        print("   • Admin Panel: http://127.0.0.1:5000/admin")
        print("   • Encryption API: http://127.0.0.1:5001")
        print("   • Storage API: http://127.0.0.1:5002")
    
    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()