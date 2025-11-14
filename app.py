import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import time
import requests
import os


app = Flask(__name__)
app.secret_key = 'your_strong_secret_key_here_for_security'

USER_DB_PATH = os.path.join('data', 'users.json')

# Backend API URLs
ENCRYPTION_API_URL = "http://127.0.0.1:5001"
STORAGE_API_URL = "http://127.0.0.1:5002"

def load_users():
    try:
        with open(USER_DB_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        save_users([])
        return []

def save_users(users):
    with open(USER_DB_PATH, 'w') as f:
        json.dump(users, f, indent=4)

def mark_user_voted(user_id):
    users = load_users()
    for user in users:
        if user['id'] == user_id:
            user['voted'] = True
            save_users(users)
            return True
    return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash('Please log in to access the voting interface.', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('id')
        password = request.form.get('password')
        users = load_users()
        
        user_match = next((u for u in users if u['id'] == user_id and u['password'] == password), None)
        
        if user_match:
            if user_match['voted']:
                flash(f"Error: Voter ID {user_id} has already cast a vote.", 'warning')
                return render_template('login.html')
            
            session['user_id'] = user_id
            session['logged_in'] = True
            flash('Login successful.', 'success')
            return redirect(url_for('vote'))
        else:
            flash('Invalid Voter ID or Password.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form.get('id')
        password = request.form.get('password')
        users = load_users()
        
        if any(u['id'] == user_id for u in users):
            flash('This Voter ID is already registered.', 'danger')
        else:
            users.append({"id": user_id, "password": password, "voted": False})
            save_users(users)
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/vote')
@login_required
def vote():
    user_id = session.get('user_id')
    users = load_users()
    if next((u['voted'] for u in users if u['id'] == user_id), False):
        flash("You have already cast your vote. Thank you!", 'warning')
        return redirect(url_for('confirmation'))
    
    return render_template('vote.html')

@app.route('/submit_vote', methods=['POST'])
@login_required
def submit_vote():
    user_id = session.get('user_id')
    selected_candidate = request.form.get('candidate')
    current_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    
    if not selected_candidate:
        flash("Error: Please select a candidate.", 'danger')
        return redirect(url_for('vote'))
    
    users = load_users()
    if next((u['voted'] for u in users if u['id'] == user_id), False):
        flash("Double voting attempt detected. Action blocked.", 'danger')
        return redirect(url_for('confirmation'))
    
    vote_data = {
        'voter_id': user_id,
        'candidate': selected_candidate,
        'timestamp': current_timestamp
    }
    
    try:
        encryption_response = requests.post(
            f"{ENCRYPTION_API_URL}/encrypt_vote",
            json=vote_data,
            timeout=10
        )
        
        encryption_response.raise_for_status()
        encrypted_vote_data = encryption_response.json()
        
        if not encrypted_vote_data.get('success'):
            error_msg = encrypted_vote_data.get('error', 'Unknown error')
            raise ValueError(f"Encryption failed: {error_msg}")
        
        encrypted_vote = encrypted_vote_data.get('encrypted_vote')
        if not encrypted_vote:
            raise ValueError("Invalid response format from Encryption API.")
    
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Encryption API: {e}")
        flash('Error: Secure encryption failed. Please try again.', 'danger')
        return redirect(url_for('vote'))
    
    except ValueError as e:
        print(f"Error processing response: {e}")
        flash('Error: Encryption API returned invalid data.', 'danger')
        return redirect(url_for('vote'))
    
    ledger_data = {
        'voter_id': user_id,
        'encrypted_vote': encrypted_vote,
        'timestamp': current_timestamp
    }
    
    try:
        storage_response = requests.post(
            f"{STORAGE_API_URL}/store_vote",
            json=ledger_data,
            timeout=10
        )
        
        storage_response.raise_for_status()
        storage_result = storage_response.json()
        
        if not storage_result.get('success'):
            error_msg = storage_result.get('error', 'Unknown error')
            raise ValueError(f"Storage failed: {error_msg}")
        
        vote_hash = storage_result.get('vote_hash', 'N/A')
        tallying_in_progress = storage_result.get('tallying_in_progress', False)
    
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Storage API: {e}")
        flash('CRITICAL ERROR: Vote encrypted but failed to store in ledger.', 'danger')
        return redirect(url_for('vote'))
    
    except ValueError as e:
        print(f"Error processing response: {e}")
        flash('CRITICAL ERROR: Storage API returned invalid response.', 'danger')
        return redirect(url_for('vote'))
    
    mark_user_voted(user_id)
    
    session['vote_success'] = True
    session['vote_candidate'] = selected_candidate
    session['vote_timestamp'] = current_timestamp
    session['vote_hash'] = vote_hash
    session['tallying_in_progress'] = tallying_in_progress
    
    if tallying_in_progress:
        flash('Your vote has been securely recorded. Tallying is in progress - your vote will be counted in the next tally!', 'success')
    else:
        flash('Your vote has been securely recorded and time-locked.', 'success')
    
    return redirect(url_for('confirmation'))

@app.route('/confirmation')
def confirmation():
    if session.get('vote_success'):
        candidate = session.get('vote_candidate', 'N/A')
        timestamp = session.get('vote_timestamp', 'N/A')
        vote_hash = session.get('vote_hash', 'N/A')
        tallying_in_progress = session.get('tallying_in_progress', False)
        
        session.pop('vote_success', None)
        session.pop('tallying_in_progress', None)
        
        message = f"Thank you! Your vote for Candidate {candidate} is confirmed."
        details = f"Submission Time: {timestamp}\n Vote Hash: {vote_hash[:16]}...\n The vote is encrypted and stored in the secure ledger."
        
        if tallying_in_progress:
            details += "\n\nNote: Tallying is currently in progress. Your vote will be included in the next count."
    else:
        message = "Vote status check."
        details = "Your status is pending or you have already voted."
    
    return render_template('confirmation.html', message=message, details=details)

# ============ ADMIN PANEL ============

@app.route('/admin')
def admin():
    """Admin panel for viewing stats and tallying results"""
    return render_template('admin.html')


# ============ API PROXY ROUTES (to avoid CORS) ============

@app.route('/api/ledger', methods=['GET'])
def api_ledger():
    """Proxy to storage service ledger endpoint"""
    try:
        response = requests.get(f"{STORAGE_API_URL}/ledger", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to storage service: {e}")
        return jsonify({
            "error": "Storage service unavailable",
            "metadata": {"total_votes": 0}
        }), 503


@app.route('/api/results', methods=['GET'])
def api_results():
    """Proxy to storage service results endpoint"""
    try:
        response = requests.get(f"{STORAGE_API_URL}/get_results", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to storage service: {e}")
        return jsonify({
            "success": False,
            "error": "Storage service unavailable"
        }), 503


@app.route('/api/tally', methods=['POST'])
def api_tally():
    """Proxy to storage service tally endpoint"""
    try:
        data = request.get_json()
        response = requests.post(
            f"{STORAGE_API_URL}/tally_results",
            json=data,
            timeout=120  # Longer timeout for tallying
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to storage service: {e}")
        return jsonify({
            "success": False,
            "error": f"Storage service unavailable: {str(e)}"
        }), 503


@app.route('/api/tally_status', methods=['GET'])
def api_tally_status():
    """NEW: Proxy to storage service tally status endpoint"""
    try:
        response = requests.get(f"{STORAGE_API_URL}/tally_status", timeout=5)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to storage service: {e}")
        return jsonify({
            "error": "Storage service unavailable",
            "tallying_in_progress": False,
            "total_votes": 0,
            "tallied_votes": 0,
            "new_votes_pending": 0
        }), 503


if __name__ == '__main__':
    load_users()
    
    print("="*60)
    print("Frontend & Authentication Service")
    print("Version 2.0 - Continuous Voting Support")
    print("Running on http://127.0.0.1:5000")
    print("Admin Panel: http://127.0.0.1:5000/admin")
    print("="*60)
    
    app.run(debug=True, port=5000)