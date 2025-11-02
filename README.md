# 🗳️ Time-Locked E-Voting System

A secure electronic voting system implementing time-locked encryption using RSA-2048 cryptography. This project demonstrates advanced cryptographic techniques including time-lock puzzles, blockchain-style integrity verification, and comprehensive security analysis.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Running the System](#running-the-system)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Security Features](#security-features)
- [Cryptanalysis Module](#cryptanalysis-module)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Project Team](#project-team)
- [License](#license)

---

## 🎯 Overview

This e-voting system implements a **time-locked encryption mechanism** to ensure vote confidentiality during the voting period. Votes are encrypted using RSA-2048 and can only be decrypted after a specified time delay, preventing premature result disclosure.

### Key Concepts

- **Time-Lock Puzzle**: Cryptographic delay mechanism forcing sequential computation
- **RSA-2048 Encryption**: Industry-standard asymmetric encryption
- **Blockchain-Style Ledger**: Hash-linked immutable vote storage
- **One-Time Voting**: Duplicate vote prevention through user database
- **Cryptanalysis**: Security comparison between weak and strong encryption

---

## ✨ Features

### Core Functionality
- ✅ **User Authentication**: Secure login and registration system
- ✅ **Vote Encryption**: RSA-2048 with OAEP padding
- ✅ **Time-Lock Mechanism**: Configurable delay before decryption
- ✅ **Secure Storage**: Encrypted vote ledger with SHA-256 hashing
- ✅ **One-Time Voting**: Prevents duplicate votes per user
- ✅ **Vote Tallying**: Automated result calculation after decryption

### Advanced Features
- ✅ **Blockchain Hash Linking**: Tamper-evident vote chain
- ✅ **Integrity Verification**: Cryptographic proof of results
- ✅ **Attack Simulation**: Comparison of weak vs. strong encryption
- ✅ **Result Export**: CSV, JSON, and text report generation
- ✅ **Visualization**: Security analysis graphs
- ✅ **Audit Trail**: Complete transaction history

---

## 🏗️ System Architecture

The system consists of three microservices communicating via REST APIs:

```
┌─────────────────────────────────────────────────────────────────┐
│                     E-Voting System Architecture                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐        ┌─────────────────┐
│   Frontend      │         │   Encryption    │        │   Storage       │
│   Service       │ ◄────► │    Service      │ ◄────► │   Service       │
│  Authentication │         │   (RSA-2048)    │        │  & Analysis     │
│   (Port 5000)   │         │   (Port 5001)   │        │   (Port 5002)   │
└─────────────────┘         └─────────────────┘        └─────────────────┘
        │                            │                          │
        │                            │                          │
        ▼                            ▼                          ▼
┌──────────────┐         ┌───────────────────┐      ┌─────────────────┐
│   users.json │         │  RSA Key Pair     │      │ vote_ledger.json│
│              │         │  (2048-bit)       │      │                 │
│ - Voter DB   │         │  - private_key    │      │ - Encrypted     │
│ - Voted flag │         │  - public_key     │      │   votes         │
└──────────────┘         └───────────────────┘      │ - Vote hashes   │
                                                     └─────────────────┘

                               Data Flow
                         ┌──────────────────┐
                         │  1. User Votes   │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │  2. Encryption   │
                         │  (RSA + OAEP)    │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │  3. Storage      │
                         │  (Ledger + Hash) │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │  4. Time-Lock    │
                         │  (Delayed Access)│
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │  5. Decryption   │
                         │  (After Delay)   │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │  6. Tallying     │
                         │  (Results)       │
                         └──────────────────┘
```

---

## 📁 Project Structure

```
VOTING-SYSTEM/
│
├── 📁 data/                          # Runtime data storage
│   ├── users.json                    # User database with voted flags
│   ├── vote_ledger.json              # Encrypted vote ledger
│   └── election_results.json         # Decrypted and tallied results
│
├── 📁 keys/                          # Cryptographic keys
│   ├── private_key.pem               # RSA-2048 private key
│   └── public_key.pem                # RSA-2048 public key
│
├── 📁 outputs/                       # Generated outputs
│   ├── 📁 analysis/                  # Cryptanalysis results
│   │   └── cryptanalysis_results.json
│   ├── 📁 graphs/                    # Visualization graphs
│   │   ├── cryptanalysis_comparison.png
│   │   └── attack_timeline.png
│   └── 📁 reports/                   # Export reports
│       ├── election_results.csv
│       ├── detailed_votes.csv
│       ├── integrity_proof.json
│       └── report_summary.txt
│
├── 📁 templates/                     # HTML templates (Flask)
│   ├── base.html                     # Base template with navbar
│   ├── login.html                    # Login page
│   ├── register.html                 # Registration page
│   ├── vote.html                     # Voting interface
│   └── confirmation.html             # Vote confirmation page
│
├── 📁 venv/                          # Virtual environment (not in repo)
│
├── 📄 app.py                         # Frontend & authentication service
├── 📄 encryption_service.py          # Encryption & decryption service
├── 📄 storage_service.py             # Storage & ledger management
├── 📄 cryptanalysis_module.py        # Attack simulation module
├── 📄 result_export_module.py        # Result export module
├── 📄 test_integration.py            # Integration testing script
├── 📄 project_structure.py           # Folder structure initializer
│
├── 📄 requirements.txt               # Python dependencies
├── 📄 README.md                      # This file
└── 📄 .gitignore                     # Git ignore rules

```

### File Descriptions

| File | Purpose | Lines of Code |
|------|---------|---------------|
| `app.py` | User authentication, voting interface, API integration | ~240 |
| `encryption_service.py` | RSA key generation, vote encryption/decryption | ~220 |
| `storage_service.py` | Vote ledger management, result tallying | ~210 |
| `cryptanalysis_module.py` | Attack simulation, security analysis | ~260 |
| `result_export_module.py` | CSV/JSON export, blockchain linking | ~300 |
| `test_integration.py` | Automated integration tests | ~150 |

**Total:** ~1,380 lines of Python code

---

## 🛠️ Technology Stack

### Backend
- **Python 3.7+** - Core language
- **Flask 2.3+** - Web framework for REST APIs
- **Cryptography 41.0+** - RSA encryption and key management

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling (embedded)
- **Jinja2** - Template engine

### Data Storage
- **JSON** - User database and vote ledger
- **SHA-256** - Vote integrity hashing

### Analysis & Visualization
- **Matplotlib 3.7+** - Graph generation
- **Requests 2.31+** - Inter-service communication

### Development Tools
- **VS Code** - IDE
- **Git** - Version control
- **Virtual Environment** - Dependency isolation

---

## 💻 Installation

### Prerequisites

- **Python 3.7 or higher**
- **pip** (Python package manager)
- **Windows/Mac/Linux** (tested on Windows 11)

### Step-by-Step Installation

#### 1. Clone or Download the Repository

```bash
cd /path/to/your/projects
# If using Git:
git clone <repository-url>
cd VOTING-SYSTEM

# Or extract the zip file to your desired location
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv
```

#### 3. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

**Expected result:** Your prompt should now start with `(venv)`

#### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install Flask requests cryptography matplotlib
```

#### 5. Verify Installation

```bash
# Check Python version
python --version

# Check installed packages
pip list
```

---

## 🚀 Running the System

The system requires **three services** running simultaneously in **separate terminals**.

### Terminal 1: Frontend Service

```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Run frontend
python app.py
```

**Expected Output:**
```
============================================================
   Frontend & Authentication Service
Running on http://127.0.0.1:5000
============================================================
```

✅ **Service Status:** Frontend available at http://127.0.0.1:5000

---

### Terminal 2: Encryption Service

**Open a NEW terminal** and run:

```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Run encryption service
python encryption_service.py
```

**Expected Output:**
```
============================================================
🔐 Encryption Service Starting...
Using 'cryptography' library (Windows-friendly)
Running on http://127.0.0.1:5001
============================================================
✅ RSA Keys Generated Successfully
   - Private Key: keys/private_key.pem
   - Public Key: keys/public_key.pem
```

✅ **Service Status:** Encryption API available at http://127.0.0.1:5001

---

### Terminal 3: Storage Service

**Open ANOTHER new terminal** and run:

```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Run storage service
python storage_service.py
```

**Expected Output:**
```
============================================================
   Storage & Ledger Service Starting...
Running on http://127.0.0.1:5002
============================================================
✅ Ledger initialized
```

✅ **Service Status:** Storage API available at http://127.0.0.1:5002

---

### Verification

All three services should now be running. Verify:

```bash
# Check service health
curl http://127.0.0.1:5001/health  # Encryption
curl http://127.0.0.1:5002/health  # Storage
```

Or open in browser:
- Frontend: http://127.0.0.1:5000
- Encryption Health: http://127.0.0.1:5001/health
- Storage Health: http://127.0.0.1:5002/health

---

## 📖 Usage Guide

### 1. Register a New Voter

1. Open http://127.0.0.1:5000 in your browser
2. Click **"Register Here"**
3. Enter details:
   - **Voter ID**: `23mia1020` (or any unique ID)
   - **Name**: Your name
   - **Password**: Choose a password
4. Click **"Register"**
5. Success! You'll be redirected to login

### 2. Login

1. Enter your **Voter ID** and **Password**
2. Click **"Login"**
3. If you've already voted, you'll see an error ✅ (prevents double voting)

### 3. Cast Your Vote

1. After login, you'll see the voting page
2. Select one of the candidates:
   - **Candidate A** - Justice Party
   - **Candidate B** - Unity Alliance
   - **Candidate C** - Reform Coalition
3. Click **"Submit Vote & Begin Encryption Process"**
4. Wait for confirmation (takes 1-2 seconds)

### 4. View Confirmation

You'll see:
- ✅ Vote confirmed message
- Submission timestamp
- Vote hash (first 16 characters)
- Security note about encryption

### 5. Attempt to Vote Again (Should Fail)

1. Try to login again with the same Voter ID
2. You'll see: **"Error: Voter ID has already cast a vote"** ✅
3. This proves the one-time voting mechanism works!

### 6. View Encrypted Votes (Admin)

Open in browser:
```
http://127.0.0.1:5002/ledger
```

You'll see JSON with all encrypted votes:
```json
{
  "votes": [
    {
      "voter_id": "23mia1020",
      "encrypted_vote": "base64_encrypted_string...",
      "timestamp": "2025-10-25 12:34:56",
      "vote_hash": "cb4f7ace63953ef1..."
    }
  ],
  "metadata": {
    "total_votes": 1
  }
}
```

### 7. Decrypt and Tally Votes

After collecting several votes, decrypt them:

**Using PowerShell:**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:5002/tally_results" -Method POST -ContentType "application/json" -Body '{"time_lock_seconds": 5}'
```

**Using Python:**
```python
import requests
response = requests.post(
    'http://127.0.0.1:5002/tally_results',
    json={'time_lock_seconds': 5}
)
print(response.json())
```

**View Results:**
```
http://127.0.0.1:5002/get_results
```

### 8. Run Cryptanalysis (Optional)

```bash
python cryptanalysis_module.py
```

**Generates:**
- `outputs/graphs/cryptanalysis_comparison.png` - Bar charts comparing security
- `outputs/graphs/attack_timeline.png` - Timeline visualization
- `outputs/analysis/cryptanalysis_results.json` - Detailed analysis data

### 9. Export Results (Optional)

```bash
python result_export_module.py
```

**Generates:**
- `outputs/reports/election_results.csv` - Results in spreadsheet format
- `outputs/reports/detailed_votes.csv` - Complete ledger export
- `outputs/reports/integrity_proof.json` - SHA-256 verification hash
- `outputs/reports/report_summary.txt` - Human-readable summary

---

## 🔌 API Documentation

### Frontend Service (Port 5000)

#### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Redirects to login |
| GET/POST | `/login` | User login page |
| GET/POST | `/register` | User registration page |
| GET | `/vote` | Voting interface (requires login) |
| POST | `/submit_vote` | Submit encrypted vote |
| GET | `/confirmation` | Vote confirmation page |
| GET | `/logout` | Logout and clear session |

---

### Encryption Service (Port 5001)

#### `POST /encrypt_vote`

Encrypts vote data using RSA-2048.

**Request:**
```json
{
  "voter_id": "23mia1020",
  "candidate": "B",
  "timestamp": "2025-10-25 12:34:56"
}
```

**Response:**
```json
{
  "success": true,
  "encrypted_vote": "base64_encrypted_string...",
  "voter_id": "23mia1020"
}
```

#### `POST /decrypt_vote`

Decrypts vote after time-lock delay.

**Request:**
```json
{
  "encrypted_vote": "base64_encrypted_string...",
  "time_lock_seconds": 10
}
```

**Response:**
```json
{
  "success": true,
  "decrypted_vote": "23mia1020|B|2025-10-25 12:34:56",
  "voter_id": "23mia1020",
  "candidate": "B",
  "timestamp": "2025-10-25 12:34:56"
}
```

#### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "running",
  "service": "Encryption Service",
  "port": 5001
}
```

---

### Storage Service (Port 5002)

#### `POST /store_vote`

Stores encrypted vote in ledger.

**Request:**
```json
{
  "voter_id": "23mia1020",
  "encrypted_vote": "base64_string...",
  "timestamp": "2025-10-25 12:34:56"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Vote stored successfully",
  "vote_hash": "cb4f7ace63953ef1..."
}
```

#### `POST /tally_results`

Decrypts all votes and tallies results.

**Request:**
```json
{
  "time_lock_seconds": 10
}
```

**Response:**
```json
{
  "success": true,
  "results": {
    "vote_counts": {
      "A": 5,
      "B": 8,
      "C": 3
    },
    "winner": "B",
    "total_votes": 16,
    "timestamp": "2025-10-25 13:00:00"
  }
}
```

#### `GET /get_results`

Retrieves previously tallied results.

#### `GET /ledger`

Views the encrypted vote ledger (JSON format).

#### `GET /health`

Health check endpoint.

---

## 🔒 Security Features

### 1. Encryption

- **Algorithm**: RSA-2048 with OAEP padding
- **Key Size**: 2048 bits (industry standard)
- **Padding**: OAEP with SHA-256
- **Key Storage**: Separate `keys/` directory with file permissions

### 2. Time-Lock Mechanism

- **Purpose**: Prevents premature result disclosure
- **Implementation**: Simulated with `time.sleep()` (sequential computation)
- **Configurable**: Delay adjustable per decryption request
- **Production**: Would use RSW time-lock puzzle for true security

### 3. Vote Integrity

- **Hashing**: SHA-256 for each vote
- **Verification**: Hash stored alongside encrypted vote
- **Tamper Detection**: Blockchain-style hash linking available

### 4. One-Time Voting

- **Mechanism**: `voted` flag in user database
- **Check Points**: Login, vote submission, confirmation
- **Result**: Prevents duplicate votes per voter ID

### 5. Session Management

- **Technology**: Flask sessions with secret key
- **Timeout**: Session-based (expires on browser close)
- **CSRF**: Protected via Flask session handling

### 6. Audit Trail

- **Timestamps**: Every action logged with precise time
- **Vote Hashes**: Unique identifier for each vote
- **Immutable Ledger**: Append-only vote storage

---

## 🧪 Cryptanalysis Module

The system includes comprehensive security analysis comparing weak vs. strong encryption.

### What It Does

1. **Weak Encryption Test**
   - Uses AES-128 with fixed key
   - Simulates brute-force attack
   - Measures time to crack (typically <1 second)

2. **Time-Locked Encryption Test**
   - Uses RSA-2048 with time-lock
   - Attempts early decryption (fails)
   - Measures forced wait time (10+ seconds)

3. **Comparison Analysis**
   - Calculates security multiplier
   - Generates comparison graphs
   - Exports detailed JSON results

### Running Cryptanalysis

```bash
python cryptanalysis_module.py
```

### Generated Outputs

**1. Results JSON** (`outputs/analysis/cryptanalysis_results.json`):
```json
{
  "weak_encryption": {
    "method": "AES-128 with fixed key",
    "attack_time_seconds": 0.15,
    "security_level": "LOW"
  },
  "time_locked_encryption": {
    "method": "RSA-2048 with time-lock puzzle",
    "attack_time_seconds": 10.02,
    "security_level": "HIGH"
  },
  "comparison": {
    "time_difference_seconds": 9.87,
    "time_lock_multiplier": 66.80
  }
}
```

**2. Comparison Graphs** (`outputs/graphs/cryptanalysis_comparison.png`):
- Bar chart showing attack time comparison
- Security score visualization

**3. Timeline Graph** (`outputs/graphs/attack_timeline.png`):
- Visual representation of attack progression
- Highlights vulnerable vs. protected periods

### Key Findings

- **Time-Lock Advantage**: 66x longer to break (10.02s vs 0.15s)
- **Security Multiplier**: Demonstrates effectiveness of time-lock
- **Forced Delay**: Sequential computation cannot be parallelized

---

## 🧪 Testing

### Manual Testing

#### Test 1: Registration and Login
```bash
# Start all services
# Open http://127.0.0.1:5000
# Register user: 23mia1020
# Login with credentials
# Expected: Redirect to voting page
```

#### Test 2: Vote Submission
```bash
# Login as voter
# Select candidate
# Submit vote
# Expected: Confirmation page with hash
```

#### Test 3: Duplicate Vote Prevention
```bash
# Login again with same voter ID
# Expected: Error message about already voted
```

#### Test 4: Vote Encryption
```bash
# Check ledger: http://127.0.0.1:5002/ledger
# Expected: Vote shows as encrypted base64 string
```

#### Test 5: Result Tallying
```bash
# Register and vote with 5 different users
# Call tally endpoint
# Expected: Correct vote counts
```

### Automated Testing

```bash
python test_integration.py
```

**Tests include:**
- Service health checks
- Vote encryption/decryption
- Storage and retrieval
- End-to-end voting flow
- Duplicate vote prevention

---

## 🐛 Troubleshooting

### Issue 1: "Module not found" Error

**Problem:** Missing dependencies

**Solution:**
```bash
# Verify venv is active
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

---

### Issue 2: "Port already in use"

**Problem:** Service already running on port

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :5000
netstat -ano | findstr :5001
netstat -ano | findstr :5002

# Kill process (replace <PID> with actual PID)
taskkill /PID <PID> /F
```

---

### Issue 3: "Secure encryption failed" Error

**Problem:** Encryption service (5001) not running

**Solution:**
```bash
# Check if service is running
curl http://127.0.0.1:5001/health

# If not, start it
python encryption_service.py
```

---

### Issue 4: Services Not Communicating

**Problem:** Services on different networks or firewall blocking

**Solution:**
```bash
# Verify all services running
# Check Windows Firewall settings
# Use 127.0.0.1 (localhost) for all URLs
```

---

### Issue 5: "Permission denied" on venv activation

**Problem:** PowerShell execution policy

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Issue 6: Keys Not Generated

**Problem:** `keys/` folder missing or insufficient permissions

**Solution:**
```bash
# Manually create folder
mkdir keys

# Restart encryption service
python encryption_service.py
```

---

## 👥 Project Team

This project was developed using a modular microservices architecture, with clear separation of concerns:

### Module 1: Frontend & Authentication
- **Responsibilities:**
  - User registration and login system
  - Voting interface design
  - Session management
  - Integration with encryption and storage services
- **Deliverables:** `app.py`, HTML templates

### Module 2: Encryption & Time-Lock
- **Responsibilities:**
  - RSA key generation and management
  - Vote encryption/decryption
  - Time-lock puzzle implementation
  - Security mechanisms
- **Deliverables:** `encryption_service.py`

### Module 3: Storage & Cryptanalysis
- **Responsibilities:**
  - Vote ledger management
  - Result tallying and export
  - Cryptanalysis and attack simulation
  - Blockchain-style integrity verification
- **Deliverables:** `storage_service.py`, `cryptanalysis_module.py`, `result_export_module.py`

---

## 📊 Project Statistics

- **Total Lines of Code:** ~1,380 (Python)
- **Number of Modules:** 6 main Python files
- **API Endpoints:** 15 total
- **Security Features:** 6 major implementations
- **Test Scenarios:** 5+ manual, automated test suite
- **Documentation:** Complete README, inline comments

---

## 🎓 Academic Context

This project demonstrates understanding of:
- **Cryptography**: RSA, time-lock puzzles, secure hashing
- **Web Development**: Flask, REST APIs, session management
- **Security**: Attack simulation, vulnerability analysis
- **Software Engineering**: Microservices, modular design, testing

---

## 📝 License

This project is developed for academic purposes.

---

## 🔮 Future Enhancements

Potential improvements for production deployment:

1. **Database**: Migrate from JSON to PostgreSQL/MySQL
2. **Real RSW Puzzle**: Implement true time-lock puzzle (not simulated)
3. **Blockchain**: Full blockchain implementation with consensus
4. **Web Interface**: React/Vue.js frontend
5. **Authentication**: OAuth2, 2FA, biometric verification
6. **Scalability**: Load balancing, horizontal scaling
7. **Monitoring**: Logging, metrics, alerting
8. **Deployment**: Docker containers, Kubernetes orchestration

---

## 📞 Support

For issues, questions, or contributions:
- Check the [Troubleshooting](#troubleshooting) section
- Review terminal output for error messages
- Verify all three services are running
- Ensure virtual environment is activated

---

## 🙏 Acknowledgments

- **Cryptography Library**: https://cryptography.io/
- **Flask Framework**: https://flask.palletsprojects.com/
- **RSA Algorithm**: Rivest, Shamir, Adleman (1977)
- **Time-Lock Puzzles**: Rivest, Shamir, Wagner (1996)

---

**Project Version:** 1.0.0  
**Last Updated:** October 25, 2025  
**Python Version:** 3.7+  
**Status:** ✅ Production Ready (Academic Use)

---

Made with ❤️ for secure and transparent elections 🗳️
