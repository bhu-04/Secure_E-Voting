"""
Quick Integration Test Script
Run this after all three services are running to verify integration
"""

import requests
import time

BASE_URL_A = "http://127.0.0.1:5000"
BASE_URL_B = "http://127.0.0.1:5001"
BASE_URL_C = "http://127.0.0.1:5002"

def test_health_checks():
    """Test if all services are running"""
    print("\n" + "="*60)
    print("🔍 Testing Service Health...")
    print("="*60)
    
    services = [
        ("Encryption", f"{BASE_URL_B}/health"),
        ("Storage", f"{BASE_URL_C}/health")
    ]
    
    all_healthy = True
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Running")
            else:
                print(f"❌ {name}: Failed (Status {response.status_code})")
                all_healthy = False
        except Exception as e:
            print(f"❌ {name}: Not reachable - {str(e)}")
            all_healthy = False
    
    return all_healthy


def test_encryption():
    """Test vote encryption"""
    print("\n" + "="*60)
    print("🔐 Testing Vote Encryption...")
    print("="*60)
    
    test_vote = {
        "voter_id": "TEST_001",
        "candidate": "A",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        response = requests.post(
            f"{BASE_URL_B}/encrypt_vote",
            json=test_vote,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Vote encrypted successfully")
                print(f"   Encrypted data (first 50 chars): {data['encrypted_vote'][:50]}...")
                return data['encrypted_vote']
            else:
                print(f"❌ Encryption failed: {data.get('error')}")
                return None
        else:
            print(f"❌ Encryption service returned status {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Encryption error: {str(e)}")
        return None


def test_storage(encrypted_vote):
    """Test vote storage"""
    print("\n" + "="*60)
    print("💾 Testing Vote Storage...")
    print("="*60)
    
    if not encrypted_vote:
        print("⚠️  Skipping storage test (no encrypted vote)")
        return False
    
    storage_data = {
        "voter_id": "TEST_001",
        "encrypted_vote": encrypted_vote,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        response = requests.post(
            f"{BASE_URL_C}/store_vote",
            json=storage_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Vote stored successfully")
                print(f"   Vote hash: {data['vote_hash'][:32]}...")
                return True
            else:
                print(f"❌ Storage failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Storage service returned status {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Storage error: {str(e)}")
        return False


def test_ledger_view():
    """Test ledger viewing"""
    print("\n" + "="*60)
    print("📋 Testing Ledger View...")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL_C}/ledger", timeout=10)
        
        if response.status_code == 200:
            ledger = response.json()
            vote_count = len(ledger.get("votes", []))
            print(f"✅ Ledger accessible")
            print(f"   Total votes stored: {vote_count}")
            return True
        else:
            print(f"❌ Ledger view failed (Status {response.status_code})")
            return False
    
    except Exception as e:
        print(f"❌ Ledger view error: {str(e)}")
        return False


def test_decryption():
    """Test vote decryption and tallying"""
    print("\n" + "="*60)
    print("🔓 Testing Vote Decryption & Tallying...")
    print("="*60)
    print("⚠️  This will take ~5 seconds due to time-lock delay...")
    
    try:
        response = requests.post(
            f"{BASE_URL_C}/tally_results",
            json={"time_lock_seconds": 5},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                results = data.get("results", {})
                print(f"✅ Decryption and tallying successful")
                print(f"   Vote counts: {results.get('vote_counts')}")
                print(f"   Winner: {results.get('winner')}")
                return True
            else:
                print(f"❌ Tallying failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Tally service returned status {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Decryption error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 E-VOTING SYSTEM INTEGRATION TEST")
    print("="*60)
    print("Make sure all three services are running:")
    print(" (app.py) on port 5000")
    print(" (encryption_service.py) on port 5001")
    print("  storage_service.py) on port 5002")
    print("="*60)
    
    input("\nPress Enter to start tests...")
    
    # Test 1: Health checks
    if not test_health_checks():
        print("\n❌ Health checks failed. Make sure all services are running.")
        return
    
    # Test 2: Encryption
    encrypted_vote = test_encryption()
    
    # Test 3: Storage
    if encrypted_vote:
        test_storage(encrypted_vote)
    
    # Test 4: Ledger view
    test_ledger_view()
    
    # Test 5: Decryption (optional - takes time)
    print("\n" + "="*60)
    choice = input("Do you want to test decryption? (takes ~5 seconds) [y/N]: ")
    if choice.lower() == 'y':
        test_decryption()
    
    print("\n" + "="*60)
    print("✅ Integration tests completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
