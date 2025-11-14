# ---------------------------------------------------------------
# Vote Storage & Ledger Service
# Runs on Port 5002
# MODIFIED: Supports continuous voting during time-lock
# ---------------------------------------------------------------

from flask import Flask, request, jsonify
import json
import os
os.makedirs('data', exist_ok=True)
import hashlib
from datetime import datetime
import requests
import time 
import threading

# Import necessary cryptography components to decrypt locally
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import base64

app = Flask(__name__)

LEDGER_FILE = os.path.join("data", "vote_ledger.json")
RESULTS_FILE = os.path.join("data", "election_results.json")
PRIVATE_KEY_FILE = os.path.join("keys", "private_key.pem") 

# Global flag to track if tallying is in progress
tallying_in_progress = False
tallying_lock = threading.Lock()


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
                "total_votes": 0,
                "last_tallied_index": -1  # NEW: Track which votes have been tallied
            }
        }
        save_ledger(ledger)
        print("✅ Ledger initialized")
    else:
        # Ensure last_tallied_index exists in existing ledgers
        ledger = load_ledger()
        if "last_tallied_index" not in ledger.get("metadata", {}):
            ledger["metadata"]["last_tallied_index"] = -1
            save_ledger(ledger)
        print("✅ Ledger already exists")


def load_ledger():
    """Load ledger from JSON file"""
    try:
        with open(LEDGER_FILE, "r") as f:
            return json.load(f)
    except:
        return {"votes": [], "metadata": {"total_votes": 0, "last_tallied_index": -1}}


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
    
    # Create vote entry with tallied status
    vote_entry = {
        "voter_id": voter_id,
        "encrypted_vote": encrypted_vote,
        "timestamp": timestamp,
        "vote_hash": hashlib.sha256(f"{voter_id}{encrypted_vote}{timestamp}".encode()).hexdigest(),
        "tallied": False  # NEW: Track if this vote has been tallied
    }
    
    # Append to ledger
    ledger["votes"].append(vote_entry)
    ledger["metadata"]["total_votes"] = len(ledger["votes"])
    ledger["metadata"]["last_updated"] = datetime.now().isoformat()
    
    save_ledger(ledger)
    
    return True, vote_entry["vote_hash"]


# ============ Module 3: Decryption & Tallying (MODIFIED) ============
def decrypt_all_votes(time_lock_seconds=10, tally_all=False):
    """
    Decrypt votes in ledger using local decryption logic
    MODIFIED: Can either tally all votes or only new untallied votes
    
    Args:
        time_lock_seconds: Time lock duration
        tally_all: If True, retally all votes. If False, only tally new votes
    """
    ledger = load_ledger()
    
    # Determine which votes to process
    if tally_all:
        votes_to_process = ledger['votes']
        start_index = 0
        print(f"🔓 FULL TALLY: Processing all {len(votes_to_process)} votes...")
    else:
        last_tallied = ledger['metadata'].get('last_tallied_index', -1)
        votes_to_process = ledger['votes'][last_tallied + 1:]
        start_index = last_tallied + 1
        print(f"🔓 INCREMENTAL TALLY: Processing {len(votes_to_process)} new votes (from index {start_index})...")
    
    if len(votes_to_process) == 0:
        print("ℹ️  No new votes to tally")
        return []
    
    decrypted_votes = []
    failed_votes = []
    
    # Load key once outside the loop
    private_key = load_private_key_local()
    if not private_key:
        print("❌ Cannot decrypt: Private key not loaded")
        return []
    
    # Enforce Time Lock ONCE before processing
    print(f"⏳ Time lock active for {time_lock_seconds} seconds...")
    time.sleep(time_lock_seconds)
    print("✅ Time lock completed. Beginning tally.")
    
    # Process each vote
    for idx, vote_entry in enumerate(votes_to_process):
        vote_num = start_index + idx + 1
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
                print(f"✅ [{vote_num}/{len(ledger['votes'])}] Decrypted vote for Voter {voter_id} → Candidate {candidate}")
            else:
                print(f"⚠️  [{vote_num}/{len(ledger['votes'])}] Invalid format after decryption (Voter: {voter_id})")
                failed_votes.append({
                    "voter_id": voter_id,
                    "reason": "Invalid format after decryption"
                })

        except Exception as e:
            print(f"❌ [{vote_num}/{len(ledger['votes'])}] Decryption failed (Voter: {voter_id}): {str(e)}")
            failed_votes.append({
                "voter_id": voter_id,
                "reason": str(e)
            })
    
    # Update last tallied index
    if decrypted_votes:
        ledger['metadata']['last_tallied_index'] = len(ledger['votes']) - 1
        save_ledger(ledger)
    
    # Summary
    print(f"\n📊 Decryption Summary:")
    print(f"   ✅ Successfully decrypted: {len(decrypted_votes)}/{len(votes_to_process)}")
    if failed_votes:
        print(f"   ❌ Failed to decrypt: {len(failed_votes)}/{len(votes_to_process)}")
        for failed in failed_votes:
            print(f"      - Voter {failed['voter_id']}: {failed['reason']}")
    
    return decrypted_votes


def tally_votes(new_decrypted_votes, incremental=False):
    """
    Tally votes - can be incremental or full retally
    
    Args:
        new_decrypted_votes: Newly decrypted votes to add
        incremental: If True, add to existing results. If False, replace results
    """
    if incremental and os.path.exists(RESULTS_FILE):
        # Load existing results and add new votes
        with open(RESULTS_FILE, "r") as f:
            existing_results = json.load(f)
        
        vote_counts = existing_results.get("vote_counts", {})
        
        # Add new votes to existing counts
        for vote in new_decrypted_votes:
            candidate = vote["candidate"]
            vote_counts[candidate] = vote_counts.get(candidate, 0) + 1
        
        total_votes = sum(vote_counts.values())
    else:
        # Full retally - start fresh
        vote_counts = {}
        for vote in new_decrypted_votes:
            candidate = vote["candidate"]
            vote_counts[candidate] = vote_counts.get(candidate, 0) + 1
        
        total_votes = len(new_decrypted_votes)
    
    # Calculate winner
    if vote_counts:
        winner = max(vote_counts, key=vote_counts.get)
    else:
        winner = None
    
    results = {
        "vote_counts": vote_counts,
        "winner": winner,
        "total_votes": total_votes,
        "timestamp": datetime.now().isoformat(),
        "tally_type": "incremental" if incremental else "full"
    }
    
    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=4)
    
    print(f"\n✅ Results saved to {RESULTS_FILE}")
    print(f"📊 Final Tally ({results['tally_type']}):")
    for candidate, count in sorted(vote_counts.items()):
        percentage = (count / total_votes * 100) if total_votes > 0 else 0
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
        "version": "2.0 - Continuous Voting Support",
        "tallying_in_progress": tallying_in_progress,
        "endpoints": {
            "/health": "GET - Health check",
            "/ledger": "GET - View encrypted vote ledger",
            "/store_vote": "POST - Store encrypted vote (works even during tallying)",
            "/tally_results": "POST - Decrypt and tally votes (incremental or full)",
            "/get_results": "GET - View tallied results",
            "/tally_status": "GET - Check if tallying is in progress"
        }
    })

@app.route('/store_vote', methods=['POST'])
def store_vote():
    """
    Endpoint to store encrypted vote in ledger
    MODIFIED: Always accepts votes, even during tallying
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
        
        # Store in ledger (works even if tallying is in progress)
        success, result = store_encrypted_vote(voter_id, encrypted_vote, timestamp)
        
        if success:
            message = "Vote stored successfully"
            if tallying_in_progress:
                message += " (will be counted in next tally)"
            
            print(f"✅ Stored vote from voter {voter_id}" + 
                  (" [Tallying in progress - will count in next tally]" if tallying_in_progress else ""))
            
            return jsonify({
                "success": True,
                "message": message,
                "vote_hash": result,
                "tallying_in_progress": tallying_in_progress
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
    Endpoint to decrypt votes and tally results
    MODIFIED: Supports both incremental and full tallying
    """
    global tallying_in_progress
    
    with tallying_lock:
        if tallying_in_progress:
            return jsonify({
                "success": False,
                "error": "Tallying already in progress. Please wait."
            }), 409
        
        tallying_in_progress = True
    
    try:
        data = request.get_json() or {}
        time_lock_seconds = data.get('time_lock_seconds', 10)
        tally_mode = data.get('mode', 'incremental')  # 'incremental' or 'full'
        
        # Check if there are any votes to tally
        ledger = load_ledger()
        total_votes_in_ledger = len(ledger.get("votes", []))
        last_tallied = ledger['metadata'].get('last_tallied_index', -1)
        new_votes_count = total_votes_in_ledger - (last_tallied + 1)
        
        if total_votes_in_ledger == 0:
            return jsonify({
                "success": False,
                "error": "No votes in ledger to tally"
            }), 400
        
        if tally_mode == 'incremental' and new_votes_count == 0:
            return jsonify({
                "success": False,
                "error": "No new votes to tally. All votes have been counted."
            }), 400
        
        print(f"\n{'='*60}")
        print(f"📊 Starting Tallying Process ({tally_mode.upper()} mode)")
        print(f"{'='*60}")
        print(f"Total votes in ledger: {total_votes_in_ledger}")
        print(f"New votes to process: {new_votes_count}")
        
        # Decrypt votes
        tally_all = (tally_mode == 'full')
        decrypted_votes = decrypt_all_votes(time_lock_seconds, tally_all=tally_all)
        
        if not decrypted_votes:
            return jsonify({
                "success": False,
                "error": f"Failed to decrypt any votes. Check private key and vote format.",
                "total_votes_in_ledger": total_votes_in_ledger,
                "successfully_decrypted": 0
            }), 500
        
        # Tally results
        incremental = (tally_mode == 'incremental')
        results = tally_votes(decrypted_votes, incremental=incremental)
        
        print(f"{'='*60}")
        print("✅ Election results tallied successfully")
        print(f"{'='*60}\n")
        
        return jsonify({
            "success": True,
            "results": results,
            "votes_processed": len(decrypted_votes),
            "total_votes_in_ledger": total_votes_in_ledger,
            "tally_mode": tally_mode
        })
    
    except Exception as e:
        print(f"❌ Tallying error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
    finally:
        tallying_in_progress = False


@app.route('/tally_status', methods=['GET'])
def tally_status():
    """Check if tallying is currently in progress"""
    ledger = load_ledger()
    total_votes = len(ledger.get("votes", []))
    last_tallied = ledger['metadata'].get('last_tallied_index', -1)
    new_votes = total_votes - (last_tallied + 1)
    
    return jsonify({
        "tallying_in_progress": tallying_in_progress,
        "total_votes": total_votes,
        "tallied_votes": last_tallied + 1,
        "new_votes_pending": new_votes
    })


@app.route('/get_results', methods=['GET'])
def get_results():
    """Get previously tallied results"""
    try:
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, "r") as f:
                results = json.load(f)
            
            # Add pending votes info
            ledger = load_ledger()
            total_votes = len(ledger.get("votes", []))
            last_tallied = ledger['metadata'].get('last_tallied_index', -1)
            pending_votes = total_votes - (last_tallied + 1)
            
            return jsonify({
                "success": True,
                "results": results,
                "pending_votes": pending_votes,
                "tallying_in_progress": tallying_in_progress
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
        "port": 5002,
        "tallying_in_progress": tallying_in_progress
    })


# Initialize ledger on startup
init_ledger()

if __name__ == "__main__":
    print("="*60)
    print("Storage & Ledger Service Starting...")
    print("Version 2.0 - Continuous Voting Support")
    print("Running on http://127.0.0.1:5002")
    print("="*60)
    app.run(debug=True, port=5002, threaded=True)