# ---------------------------------------------------------------
# Time-Locked Encryption Service for E-Voting
# Runs on Port 5001
# FIXED VERSION - Uses 'cryptography' library + Concurrency
# ---------------------------------------------------------------

from flask import Flask, request, jsonify
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import base64
import os
os.makedirs('keys', exist_ok=True)
import time
import requests # Still needed for decrypt_vote if used directly

app = Flask(__name__)

# File paths for RSA keys
PRIVATE_KEY_FILE = os.path.join("keys", "private_key.pem")
PUBLIC_KEY_FILE = os.path.join("keys", "public_key.pem")


# ============ Module 1: Key Generation ============
def generate_keys():
    # ... (Key generation code remains unchanged) ...
    """Generate RSA key pair and save to files"""
    if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
        print("🔑 Generating new RSA key pair...")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Generate public key
        public_key = private_key.public_key()
        
        # Serialize and save private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        with open(PRIVATE_KEY_FILE, "wb") as f:
            f.write(private_pem)
        
        # Serialize and save public key
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        with open(PUBLIC_KEY_FILE, "wb") as f:
            f.write(public_pem)
        
        print("✅ RSA Keys Generated Successfully")
        print(f"   - Private Key: {PRIVATE_KEY_FILE}")
        print(f"   - Public Key: {PUBLIC_KEY_FILE}")
    else:
        print("✅ RSA Keys Already Exist")


def load_private_key():
    """Load private key from file"""
    with open(PRIVATE_KEY_FILE, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    return private_key


def load_public_key():
    """Load public key from file"""
    with open(PUBLIC_KEY_FILE, "rb") as f:
        public_key = serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )
    return public_key


# Generate keys on startup
try:
    generate_keys()
except Exception as e:
    print(f"❌ Error generating keys: {e}")


# ============ Module 2: Vote Encryption ============
def encrypt_vote_data(vote_text):
    # ... (Encryption code remains unchanged) ...
    """Encrypt a vote using RSA public key"""
    try:
        public_key = load_public_key()
        
        # Encrypt the vote
        encrypted_vote = public_key.encrypt(
            vote_text.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Convert bytes to base64 for JSON transmission
        encrypted_vote_b64 = base64.b64encode(encrypted_vote).decode('utf-8')
        
        return encrypted_vote_b64
    
    except Exception as e:
        raise Exception(f"Encryption error: {str(e)}")


# ============ Module 3: Time Lock (Function is now redundant but kept for API structure) ============
def time_lock(delay_seconds=10):
    """Simulate time-lock delay before decryption"""
    print(f"⏳ Time lock active for {delay_seconds} seconds...")
    time.sleep(delay_seconds)
    print("✅ Time lock completed")


# ============ Module 4: Vote Decryption (Now primarily for testing/single-vote checks) ============
def decrypt_vote_data(encrypted_vote_b64):
    """Decrypt an encrypted vote using RSA private key"""
    try:
        private_key = load_private_key()
        
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
    
    except Exception as e:
        raise Exception(f"Decryption error: {str(e)}")


# ============ Flask Routes ============

@app.route('/encrypt_vote', methods=['POST'])
def encrypt_vote():
    # ... (Encryption endpoint remains unchanged) ...
    """
    Endpoint for to encrypt votes
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data received"
            }), 400
        
        voter_id = data.get('voter_id')
        candidate = data.get('candidate')
        timestamp = data.get('timestamp')
        
        if not all([voter_id, candidate, timestamp]):
            return jsonify({
                "success": False,
                "error": f"Missing required fields. Got: {list(data.keys())}"
            }), 400
        
        # Create vote string
        vote_string = f"{voter_id}|{candidate}|{timestamp}"
        
        # Encrypt the vote
        encrypted_vote = encrypt_vote_data(vote_string)
        
        print(f"✅ Encrypted vote for voter {voter_id} -> Candidate {candidate}")
        
        return jsonify({
            "success": True,
            "encrypted_vote": encrypted_vote,
            "voter_id": voter_id
        })
    
    except Exception as e:
        print(f"❌ Encryption error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/decrypt_vote', methods=['POST'])
def decrypt_vote():
    # ... (Decryption endpoint remains unchanged, still includes time-lock simulation) ...
    """
    Endpoint for decrypting votes after time-lock
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data received"
            }), 400
        
        encrypted_vote = data.get('encrypted_vote')
        time_lock_seconds = data.get('time_lock_seconds', 10)
        
        if not encrypted_vote:
            return jsonify({
                "success": False,
                "error": "Missing encrypted_vote"
            }), 400
        
        # Apply time lock (Simulation)
        time_lock(time_lock_seconds)
        
        # Decrypt the vote
        decrypted_vote = decrypt_vote_data(encrypted_vote)
        
        # Parse the decrypted string
        parts = decrypted_vote.split('|')
        if len(parts) == 3:
            voter_id, candidate, timestamp = parts
            
            return jsonify({
                "success": True,
                "decrypted_vote": decrypted_vote,
                "voter_id": voter_id,
                "candidate": candidate,
                "timestamp": timestamp
            })
        else:
            return jsonify({
                "success": False,
                "error": "Invalid vote format"
            }), 400
    
    except Exception as e:
        print(f"❌ Decryption error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "service": "Encryption Service",
        "port": 5001,
        "library": "cryptography (not pycryptodome)"
    })


@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        "service": "Encryption Service",
        "status": "running",
        "endpoints": {
            "/encrypt_vote": "POST - Encrypt a vote",
            "/decrypt_vote": "POST - Decrypt a vote (with time-lock)",
            "/health": "GET - Health check"
        }
    })


if __name__ == "__main__":
    print("="*60)
    print("Encryption Service Starting...")
    print("Using 'cryptography' library (Windows-friendly)")
    print("Running on http://127.0.0.1:5001")
    print("="*60)
    # CRITICAL FIX: Enable threading to handle multiple simultaneous encryption requests
    app.run(debug=True, port=5001, use_reloader=False, threaded=True)