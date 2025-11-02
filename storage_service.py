# ---------------------------------------------------------------
# Vote Storage & Ledger Service
# Runs on Port 5002
# CRITICAL FIX: Improved error handling in decryption loop
# ---------------------------------------------------------------

from flask import Flask, request, jsonify
import json
import os
os.makedirs('data', exist_ok=True)
import hashlib
from datetime import datetime
import requests
import time 

# Import necessary cryptography components to decrypt locally
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import base64

app = Flask(__name__)

LEDGER_FILE = os.path.join("data", "vote_ledger.json")
RESULTS_FILE = os.path.join("data", "election_results.json")
PRIVATE_KEY_FILE = os.path.join("keys", "private_key.pem") 


# ============ Module 0: Local Decryption Logic ============

def load_private_key_local():
    """Load private key from file for local decryption"""
    try:
        with open(PRIVATE_KEY_FILE, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        return private_key
    except FileNotFoundError:
        print(f"❌ CRITICAL ERROR: Private key not found at {PRIVATE_KEY_FILE}. Run encryption_service.py first to generate keys.")
        return None
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Failed to load private key: {e}")
        return None

def decrypt_vote_data_local(encrypted_vote_b64, private_key):
    """Decrypt an encrypted vote using RSA private key, locally"""
    if not private_key:
        raise Exception("Private key not loaded for local decryption.")
        
    # Convert base64 back to bytes
    encrypted_vote = base64.b64decode(encrypted_vote_b64)
    
    # Decrypt the vote
    decrypted_vote = private_key.decrypt(
        encrypted_vote,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return decrypted_vote.decode()


# ============ Module 1: Ledger Initialization ============
def init_ledger():
    """Initialize empty ledger if it doesn't exist"""
    if not os.path.exists(LEDGER_FILE):
        ledger = {
            "votes": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_votes": 0
            }
        }
        save_ledger(ledger)
        print("✅ Ledger initialized")
    else:
        print("✅ Ledger already exists")


def load_ledger():
    """Load ledger from JSON file"""
    try:
        with open(LEDGER_FILE, "r") as f:
            return json.load(f)
    except:
        return {"votes": [], "metadata": {"total_votes": 0}}


def save_ledger(ledger):
    """Save ledger to JSON file"""
    with open(LEDGER_FILE, "w") as f:
        json.dump(ledger, f, indent=4)


# ============ Module 2: Vote Storage ============
def store_encrypted_vote(voter_id, encrypted_vote, timestamp):
    """Store encrypted vote in ledger with hash"""
    ledger = load_ledger()
    
    # Check for duplicate voter
    for vote in ledger["votes"]:
        if vote["voter_id"] == voter_id:
            return False, "Voter has already cast a vote"
    
    # Create vote entry
    vote_entry = {
        "voter_id": voter_id,
        "encrypted_vote": encrypted_vote,
        "timestamp": timestamp,
        "vote_hash": hashlib.sha256(f"{voter_id}{encrypted_vote}{timestamp}".encode()).hexdigest()
    }
    
    # Append to ledger
    ledger["votes"].append(vote_entry)
    ledger["metadata"]["total_votes"] = len(ledger["votes"])
    ledger["metadata"]["last_updated"] = datetime.now().isoformat()
    
    save_ledger(ledger)
    
    return True, vote_entry["vote_hash"]


# ============ Module 3: Decryption & Tallying (FIXED) ============
def decrypt_all_votes(time_lock_seconds=10):
    """
    Decrypt all votes in ledger using local decryption logic
    IMPROVED: Better error handling, continues even if some votes fail
    """
    ledger = load_ledger()
    decrypted_votes = []
    failed_votes = []
    
    # Load key once outside the loop
    private_key = load_private_key_local()
    if not private_key:
        print("❌ Cannot decrypt: Private key not loaded")
        return []
        
    total_votes = len(ledger['votes'])
    print(f"🔓 Starting LOCAL decryption of {total_votes} votes...")
    
    # Enforce Time Lock ONCE before processing
    if total_votes > 0:
        print(f"⏳ Time lock active for {time_lock_seconds} seconds...")
        time.sleep(time_lock_seconds)
        print("✅ Time lock completed. Beginning tally.")
    
    # Process each vote
    for idx, vote_entry in enumerate(ledger["votes"]):
        vote_num = idx + 1
        voter_id = vote_entry.get("voter_id", "UNKNOWN")
        
        try:
            # Decrypt Locally
            decrypted_vote_string = decrypt_vote_data_local(
                vote_entry["encrypted_vote"],
                private_key
            )
            
            # Parse the decrypted vote
            parts = decrypted_vote_string.split('|')
            if len(parts) == 3:
                parsed_voter_id, candidate, timestamp = parts
                
                decrypted_votes.append({
                    "voter_id": parsed_voter_id,
                    "candidate": candidate,
                    "timestamp": timestamp
                })
                print(f"✅ [{vote_num}/{total_votes}] Decrypted vote for Voter {voter_id} → Candidate {candidate}")
            else:
                print(f"⚠️  [{vote_num}/{total_votes}] Invalid format after decryption (Voter: {voter_id})")
                failed_votes.append({
                    "voter_id": voter_id,
                    "reason": "Invalid format after decryption"
                })

        except Exception as e:
            print(f"❌ [{vote_num}/{total_votes}] Decryption failed (Voter: {voter_id}): {str(e)}")
            failed_votes.append({
                "voter_id": voter_id,
                "reason": str(e)
            })
    
    # Summary
    print(f"\n📊 Decryption Summary:")
    print(f"   ✅ Successfully decrypted: {len(decrypted_votes)}/{total_votes}")
    if failed_votes:
        print(f"   ❌ Failed to decrypt: {len(failed_votes)}/{total_votes}")
        for failed in failed_votes:
            print(f"      - Voter {failed['voter_id']}: {failed['reason']}")
    
    return decrypted_votes


def tally_votes(decrypted_votes):
    """Tally decrypted votes and return results"""
    vote_counts = {}
    
    for vote in decrypted_votes:
        candidate = vote["candidate"]
        vote_counts[candidate] = vote_counts.get(candidate, 0) + 1
    
    # Calculate winner
    if vote_counts:
        winner = max(vote_counts, key=vote_counts.get)
    else:
        winner = None
    
    results = {
        "vote_counts": vote_counts,
        "winner": winner,
        "total_votes": len(decrypted_votes),
        "timestamp": datetime.now().isoformat()
    }
    
    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=4)
    
    print(f"\n✅ Results saved to {RESULTS_FILE}")
    print(f"📊 Final Tally:")
    for candidate, count in sorted(vote_counts.items()):
        percentage = (count / len(decrypted_votes) * 100) if decrypted_votes else 0
        print(f"   Candidate {candidate}: {count} votes ({percentage:.1f}%)")
    if winner:
        print(f"🏆 Winner: Candidate {winner}")
    
    return results


# ============ Flask Routes ============
@app.route('/', methods=['GET'])
def index():
    """Root endpoint with service information"""
    return jsonify({
        "service": "Storage & Ledger Service",
        "status": "running",
        "port": 5002,
        "version": "1.0",
        "endpoints": {
            "/health": "GET - Health check",
            "/ledger": "GET - View encrypted vote ledger",
            "/store_vote": "POST - Store encrypted vote",
            "/tally_results": "POST - Decrypt and tally all votes",
            "/get_results": "GET - View tallied results"
        },
        "usage": {
            "view_ledger": "http://127.0.0.1:5002/ledger",
            "view_results": "http://127.0.0.1:5002/get_results",
            "health_check": "http://127.0.0.1:5002/health"
        }
    })

@app.route('/store_vote', methods=['POST'])
def store_vote():
    """
    Endpoint to store encrypted vote in ledger
    """
    try:
        data = request.get_json()
        voter_id = data.get('voter_id')
        encrypted_vote = data.get('encrypted_vote')
        timestamp = data.get('timestamp')
        
        if not all([voter_id, encrypted_vote, timestamp]):
            return jsonify({
                "success": False,
                "error": "Missing required fields"
            }), 400
        
        # Store in ledger
        success, result = store_encrypted_vote(voter_id, encrypted_vote, timestamp)
        
        if success:
            print(f"✅ Stored vote from voter {voter_id}")
            return jsonify({
                "success": True,
                "message": "Vote stored successfully",
                "vote_hash": result
            })
        else:
            return jsonify({
                "success": False,
                "error": result
            }), 400
    
    except Exception as e:
        print(f"❌ Storage error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/tally_results', methods=['POST'])
def tally_results():
    """
    Endpoint to decrypt all votes and tally results
    IMPROVED: Better error messages and handling
    """
    try:
        data = request.get_json() or {}
        time_lock_seconds = data.get('time_lock_seconds', 10)
        
        # Check if there are any votes to tally
        ledger = load_ledger()
        total_votes_in_ledger = len(ledger.get("votes", []))
        
        if total_votes_in_ledger == 0:
            return jsonify({
                "success": False,
                "error": "No votes in ledger to tally"
            }), 400
        
        print(f"\n{'='*60}")
        print(f"📊 Starting Tallying Process")
        print(f"{'='*60}")
        print(f"Total votes to process: {total_votes_in_ledger}")
        
        # Decrypt all votes
        decrypted_votes = decrypt_all_votes(time_lock_seconds)
        
        if not decrypted_votes:
            return jsonify({
                "success": False,
                "error": f"Failed to decrypt any votes. Check private key and vote format.",
                "total_votes_in_ledger": total_votes_in_ledger,
                "successfully_decrypted": 0
            }), 500
        
        # Tally results
        results = tally_votes(decrypted_votes)
        
        print(f"{'='*60}")
        print("✅ Election results tallied successfully")
        print(f"{'='*60}\n")
        
        return jsonify({
            "success": True,
            "results": results,
            "total_votes_decrypted": len(decrypted_votes),
            "total_votes_in_ledger": total_votes_in_ledger
        })
    
    except Exception as e:
        print(f"❌ Tallying error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/get_results', methods=['GET'])
def get_results():
    """Get previously tallied results"""
    try:
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, "r") as f:
                results = json.load(f)
            return jsonify({
                "success": True,
                "results": results
            })
        else:
            return jsonify({
                "success": False,
                "error": "No results available yet. Run /tally_results first."
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/ledger', methods=['GET'])
def view_ledger():
    """View the encrypted vote ledger"""
    ledger = load_ledger()
    return jsonify(ledger)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "service": "Storage & Ledger Service",
        "port": 5002
    })


# Initialize ledger on startup
init_ledger()

if __name__ == "__main__":
    print("="*60)
    print("Storage & Ledger Service Starting...")
    print("Running on http://127.0.0.1:5002")
    print("="*60)
    app.run(debug=True, port=5002, threaded=True)