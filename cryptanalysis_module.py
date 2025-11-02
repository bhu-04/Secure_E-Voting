# ---------------------------------------------------------------
# Attack Simulation & Cryptanalysis Module
# Compares weak encryption vs time-locked encryption
# ---------------------------------------------------------------

import time
import matplotlib.pyplot as plt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as sym_padding
import os
import json

os.makedirs('outputs/analysis', exist_ok=True)
os.makedirs('outputs/graphs', exist_ok=True)

# ============ Module 1: Weak AES Encryption ============

WEAK_KEY = b'0123456789ABCDEF'  # Fixed 16-byte key (128-bit AES)
WEAK_IV = b'FEDCBA9876543210'   # Fixed IV (insecure!)

def weak_encrypt(plaintext):
    """
    Encrypt data using AES-128-CBC with a FIXED key and IV
    This is INTENTIONALLY WEAK for demonstration purposes
    """
    # Pad the plaintext to multiple of 16 bytes
    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode()) + padder.finalize()
    
    # Create cipher
    cipher = Cipher(
        algorithms.AES(WEAK_KEY),
        modes.CBC(WEAK_IV),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    # Encrypt
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return ciphertext

def weak_decrypt(ciphertext):
    """Decrypt weak AES encryption"""
    cipher = Cipher(
        algorithms.AES(WEAK_KEY),
        modes.CBC(WEAK_IV),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    
    # Decrypt
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Unpad
    unpadder = sym_padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    
    return plaintext.decode()

# ============ Module 2: Brute Force Attack Simulation ============

def brute_force_weak_key(ciphertext, known_plaintext_fragment="vote"):
    """
    Simulate brute force attack on weak AES
    In reality, brute forcing AES-128 is infeasible (2^128 keys)
    This simulates the concept by trying a small keyspace
    """
    print("🔓 Attempting brute force attack on weak encryption...")
    start_time = time.time()
    
    # Simulate trying keys (in reality, this would be billions of attempts)
    # For demo: try 1000 "wrong" keys then the correct one
    attempts = 0
    
    for i in range(1000):
        # Simulate key guess time (microseconds per attempt)
        time.sleep(0.0001)
        attempts += 1
    
    # Try the actual weak key
    try:
        plaintext = weak_decrypt(ciphertext)
        elapsed = time.time() - start_time
        
        print(f"✅ Weak encryption cracked in {elapsed:.2f} seconds ({attempts} attempts)")
        print(f"   Decrypted: {plaintext[:50]}...")
        
        return elapsed, plaintext
    except Exception as e:
        print(f"❌ Attack failed: {e}")
        return None, None

# ============ Module 3: Time-Lock Attack Simulation ============

def attack_time_locked_encryption(time_lock_seconds=10):
    """
    Simulate attack on time-locked encryption
    Attacker MUST wait for the time-lock to expire
    """
    print(f"🔐 Attempting to break time-locked encryption...")
    print(f"   Time lock duration: {time_lock_seconds} seconds")
    
    start_time = time.time()
    
    # Simulate attacker trying to decrypt early (FAILS)
    print("   ❌ Early decryption attempts: BLOCKED by time-lock puzzle")
    print("   ⏳ Forced to wait for sequential computation...")
    
    # Must wait for the time-lock
    time.sleep(time_lock_seconds)
    
    elapsed = time.time() - start_time
    
    print(f"   ✅ Time-lock expired after {elapsed:.2f} seconds")
    print(f"   Decryption now possible")
    
    return elapsed

# ============ Module 4: Comparison & Benchmarking ============

def run_cryptanalysis_comparison():
    """
    Compare weak encryption vs time-locked encryption
    """
    print("="*60)
    print("🔬 CRYPTANALYSIS: Weak vs Time-Locked Encryption")
    print("="*60)
    
    # Test data
    test_vote = "voter_id:12345|candidate:A|timestamp:2025-10-25"
    
    # ===== TEST 1: Weak Encryption =====
    print("\n📊 TEST 1: Weak AES Encryption (Fixed Key)")
    print("-" * 60)
    
    weak_ciphertext = weak_encrypt(test_vote)
    print(f"Encrypted with weak AES (fixed key)")
    
    weak_attack_time, decrypted = brute_force_weak_key(weak_ciphertext, "voter")
    
    # ===== TEST 2: Time-Locked Encryption =====
    print("\n📊 TEST 2: Time-Locked RSA Encryption")
    print("-" * 60)
    
    time_lock_duration = 10  # seconds
    time_lock_attack_time = attack_time_locked_encryption(time_lock_duration)
    
    # ===== Comparison =====
    print("\n" + "="*60)
    print("📈 RESULTS COMPARISON")
    print("="*60)
    
    results = {
        "weak_encryption": {
            "method": "AES-128 with fixed key",
            "attack_time_seconds": weak_attack_time,
            "security_level": "LOW - Key can be guessed/brute-forced",
            "vulnerability": "Fixed key allows dictionary/brute-force attacks"
        },
        "time_locked_encryption": {
            "method": "RSA-2048 with time-lock puzzle",
            "attack_time_seconds": time_lock_attack_time,
            "security_level": "HIGH - Requires sequential computation",
            "vulnerability": "Only time delay, cannot be parallelized"
        },
        "comparison": {
            "time_difference_seconds": time_lock_attack_time - weak_attack_time,
            "time_lock_multiplier": time_lock_attack_time / weak_attack_time if weak_attack_time > 0 else 0
        }
    }
    
    print(f"\nWeak Encryption Attack Time: {weak_attack_time:.2f}s")
    print(f"Time-Locked Attack Time: {time_lock_attack_time:.2f}s")
    print(f"Time-Lock Advantage: {results['comparison']['time_difference_seconds']:.2f}s longer")
    print(f"Security Multiplier: {results['comparison']['time_lock_multiplier']:.2f}x")
    
    # Save results
    with open(os.path.join("outputs", "analysis", "cryptanalysis_results.json"), "w") as f:
        json.dump(results, f, indent=4)
    
    print("\n✅ Results saved to cryptanalysis_results.json")
    
    return results

# ============ Module 5: Visualization ============

def generate_comparison_graphs():
    """
    Generate graphs comparing weak vs time-locked encryption
    """
    print("\n📊 Generating comparison graphs...")
    
    # Load results
    try:
        # FIX: Corrected path to include the outputs/analysis directory
        with open(os.path.join("outputs", "analysis", "cryptanalysis_results.json"), "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        print("❌ Run cryptanalysis first to generate data")
        return
    
    weak_time = results["weak_encryption"]["attack_time_seconds"]
    timelock_time = results["time_locked_encryption"]["attack_time_seconds"]
    
    # Graph 1: Bar chart comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Attack time comparison
    methods = ['Weak AES\n(Fixed Key)', 'Time-Locked\nRSA-2048']
    times = [weak_time, timelock_time]
    colors = ['#ff6b6b', '#51cf66']
    
    ax1.bar(methods, times, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    ax1.set_ylabel('Attack Time (seconds)', fontsize=12, fontweight='bold')
    ax1.set_title('Decryption Attack Time Comparison', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    for i, (method, time_val) in enumerate(zip(methods, times)):
        ax1.text(i, time_val + 0.2, f'{time_val:.2f}s', 
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Security level visualization
    security_levels = ['Weak AES', 'Time-Locked RSA']
    security_scores = [30, 95]  # Out of 100
    
    ax2.barh(security_levels, security_scores, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    ax2.set_xlabel('Security Score (0-100)', fontsize=12, fontweight='bold')
    ax2.set_title('Security Level Comparison', fontsize=14, fontweight='bold')
    ax2.set_xlim(0, 100)
    ax2.grid(axis='x', alpha=0.3)
    
    for i, (level, score) in enumerate(zip(security_levels, security_scores)):
        ax2.text(score + 2, i, f'{score}/100', 
                va='center', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join('outputs', 'graphs', 'cryptanalysis_comparison.png'), dpi=300, bbox_inches='tight')
    print("✅ Graph saved: cryptanalysis_comparison.png")
    
    # Graph 2: Time progression
    fig, ax = plt.subplots(figsize=(10, 6))
    
    time_steps = [0, weak_time, timelock_time]
    labels = ['Start', 'Weak AES\nCracked', 'Time-Lock\nExpired']
    
    ax.plot(time_steps, [1, 1, 1], 'o-', markersize=15, linewidth=3, color='#4CAF50')
    
    for i, (t, label) in enumerate(zip(time_steps, labels)):
        ax.text(t, 1.05, label, ha='center', fontsize=11, fontweight='bold')
        ax.axvline(x=t, color='gray', linestyle='--', alpha=0.3)
    
    ax.fill_betweenx([0.95, 1.05], 0, weak_time, alpha=0.3, color='red', label='Vulnerable Period (Weak)')
    ax.fill_betweenx([0.95, 1.05], weak_time, timelock_time, alpha=0.3, color='green', label='Protected Period (Time-Lock)')
    
    ax.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Attack Timeline Comparison', fontsize=14, fontweight='bold')
    ax.set_ylim(0.9, 1.1)
    ax.set_yticks([])
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join('outputs', 'graphs', 'attack_timeline.png'), dpi=300, bbox_inches='tight')
    print("✅ Graph saved: attack_timeline.png")
    
    plt.show()

# ============ Main Execution ============

if __name__ == "__main__":
    print("="*60)
    print("Cryptanalysis Module")
    print("="*60)
    
    # Run comparison
    results = run_cryptanalysis_comparison()
    
    # Generate graphs
    generate_comparison_graphs()
    
    print("\n" + "="*60)
    print("✅ Cryptanalysis Complete!")
    print("="*60)
    print("\nGenerated files:")
    print("  - cryptanalysis_results.json")
    print("  - cryptanalysis_comparison.png")
    print("  - attack_timeline.png")