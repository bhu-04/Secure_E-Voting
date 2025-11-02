# ---------------------------------------------------------------
# Result Publishing & Export Module
# Export results as CSV/JSON with integrity proofs
# FIXED VERSION - Corrects JSON keys for CSV export and Summary
# ---------------------------------------------------------------

import json
import csv
import hashlib
from datetime import datetime
import os

os.makedirs('outputs/reports', exist_ok=True)
os.makedirs('data', exist_ok=True)

# ============ Module 1: Result Export to CSV ============
def export_results_to_csv(
    results_file=os.path.join("data", "election_results.json"),
    output_file=os.path.join("outputs", "reports", "election_results.csv")
):
    """
    Export election results to CSV format
    """
    try:
        # Load results
        with open(results_file, "r") as f:
            results = json.load(f)
        
        # Create CSV
        with open(output_file, "w", newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(["Election Results Export"])
            writer.writerow(["Generated:", results.get("timestamp", "N/A")])
            writer.writerow([])
            
            # Vote counts
            writer.writerow(["Candidate", "Votes", "Percentage"])
            
            # FIX START: Corrected keys to match the JSON structure from storage_service.py
            total_votes = results.get("total_votes", 0) 
            vote_counts = results.get("vote_counts", {})
            # FIX END
            
            for candidate, count in sorted(vote_counts.items()):
                percentage = (count / total_votes * 100) if total_votes > 0 else 0
                writer.writerow([candidate, count, f"{percentage:.2f}%"])
            
            writer.writerow([])
            writer.writerow(["Total Votes", total_votes])
            writer.writerow(["Winner", results.get("winner", "N/A")])
        
        print(f"✅ Results exported to {output_file}")
        return output_file
    
    except FileNotFoundError:
        print(f"❌ Error: {results_file} not found. Run tallying first.")
        return None
    except Exception as e:
        print(f"❌ Error exporting to CSV: {e}")
        return None


# ============ Module 2: Detailed Vote Export ============

def export_detailed_votes_csv(
    ledger_file=os.path.join("data", "vote_ledger.json"),
    output_file=os.path.join("outputs", "reports", "detailed_votes.csv")
):
    """
    Export detailed encrypted vote ledger to CSV
    """
    try:
        with open(ledger_file, "r") as f:
            ledger = json.load(f)
        
        votes = ledger.get("votes", [])
        
        with open(output_file, "w", newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(["Vote Ledger Export"])
            writer.writerow(["Generated:", datetime.now().isoformat()])
            writer.writerow(["Total Votes:", len(votes)])
            writer.writerow([])
            
            # Column headers
            writer.writerow(["#", "Voter ID", "Timestamp", "Vote Hash (SHA-256)", "Encrypted Vote (First 50 chars)"])
            
            # Vote entries
            for idx, vote in enumerate(votes, 1):
                writer.writerow([
                    idx,
                    vote.get("voter_id", "N/A"),
                    vote.get("timestamp", "N/A"),
                    vote.get("vote_hash", "N/A")[:64],  # First 64 chars of hash
                    vote.get("encrypted_vote", "N/A")[:50] + "..."  # First 50 chars of ciphertext
                ])
        
        print(f"✅ Detailed ledger exported to {output_file}")
        return output_file
    
    except FileNotFoundError:
        print(f"❌ Error: {ledger_file} not found.")
        return None
    except Exception as e:
        print(f"❌ Error exporting ledger: {e}")
        return None


# ============ Module 3: Integrity Proof Generation ============

def generate_integrity_proof(results_file=os.path.join("data", "election_results.json")):
    """
    Generate cryptographic proof of result integrity
    """
    try:
        with open(results_file, "r") as f:
            content = f.read()
        
        # Calculate SHA-256 hash
        result_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Create proof document
        proof = {
            "results_file": results_file,
            "timestamp": datetime.now().isoformat(),
            "sha256_hash": result_hash,
            "proof_message": "This hash can be used to verify the results have not been tampered with",
            "verification_instructions": "Recalculate SHA-256 of the results file and compare with this hash"
        }
        
        # Save proof
        proof_file = os.path.join("outputs", "reports", "integrity_proof.json")
        with open(proof_file, "w") as f:
            json.dump(proof, f, indent=4)
        
        print(f"✅ Integrity proof generated")
        print(f"   SHA-256: {result_hash}")
        print(f"   Saved to: {proof_file}")
        
        return proof
    
    except Exception as e:
        print(f"❌ Error generating proof: {e}")
        return None


# ============ Module 4: Blockchain-Style Hash Linking ============

def add_blockchain_style_linking(ledger_file=os.path.join("data", "vote_ledger.json")):
    """
    Add blockchain-style hash linking to vote ledger
    Each vote includes hash of previous vote (immutable chain)
    """
    try:
        with open(ledger_file, "r") as f:
            ledger = json.load(f)
        
        votes = ledger.get("votes", [])
        
        if not votes:
            print("⚠️  No votes to link")
            return
        
        # Link votes with previous hash
        previous_hash = "0" * 64  # Genesis block hash
        
        for idx, vote in enumerate(votes):
            # Add previous hash link
            vote["previous_hash"] = previous_hash
            
            # Calculate current block hash
            block_data = f"{vote['voter_id']}{vote['encrypted_vote']}{vote['timestamp']}{previous_hash}"
            current_hash = hashlib.sha256(block_data.encode()).hexdigest()
            vote["block_hash"] = current_hash
            vote["block_number"] = idx + 1
            
            # Update for next iteration
            previous_hash = current_hash
        
        # Save updated ledger
        ledger["blockchain_enabled"] = True
        ledger["chain_length"] = len(votes)
        ledger["latest_block_hash"] = previous_hash
        
        with open(ledger_file, "w") as f:
            json.dump(ledger, f, indent=4)
        
        print(f"✅ Blockchain-style linking added to {len(votes)} votes")
        print(f"   Chain length: {len(votes)}")
        print(f"   Latest block hash: {previous_hash[:32]}...")
        
        return ledger
    
    except Exception as e:
        print(f"❌ Error adding blockchain linking: {e}")
        return None


def verify_blockchain_integrity(ledger_file=os.path.join("data", "vote_ledger.json")):
    """
    Verify integrity of blockchain-linked ledger
    """
    try:
        with open(ledger_file, "r") as f:
            ledger = json.load(f)
        
        if not ledger.get("blockchain_enabled"):
            print("⚠️  Ledger is not blockchain-linked")
            return False
        
        votes = ledger.get("votes", [])
        previous_hash = "0" * 64
        
        print(f"🔍 Verifying blockchain integrity ({len(votes)} blocks)...")
        
        for idx, vote in enumerate(votes):
            # Check previous hash matches
            if vote.get("previous_hash") != previous_hash:
                print(f"❌ Block {idx + 1}: Previous hash mismatch!")
                return False
            
            # Recalculate block hash
            block_data = f"{vote['voter_id']}{vote['encrypted_vote']}{vote['timestamp']}{previous_hash}"
            calculated_hash = hashlib.sha256(block_data.encode()).hexdigest()
            
            if vote.get("block_hash") != calculated_hash:
                print(f"❌ Block {idx + 1}: Block hash mismatch! Tampering detected!")
                return False
            
            previous_hash = calculated_hash
        
        print(f"✅ Blockchain integrity verified: All {len(votes)} blocks are valid")
        return True
    
    except Exception as e:
        print(f"❌ Error verifying blockchain: {e}")
        return False


# ============ Module 5: Complete Report Generation ============

def generate_complete_report():
    """
    Generate a complete report with all exports and proofs
    """
    print("="*60)
    print("📊 Generating Complete Election Report")
    print("="*60)
    
    report_files = []
    
    # 1. Export results to CSV
    print("\n1. Exporting results to CSV...")
    csv_file = export_results_to_csv()
    if csv_file:
        report_files.append(csv_file)
    
    # 2. Export detailed vote ledger
    print("\n2. Exporting detailed vote ledger...")
    ledger_csv = export_detailed_votes_csv()
    if ledger_csv:
        report_files.append(ledger_csv)
    
    # 3. Generate integrity proof
    print("\n3. Generating integrity proof...")
    proof = generate_integrity_proof()
    if proof:
        report_files.append("integrity_proof.json")
    
    # 4. Add blockchain linking
    print("\n4. Adding blockchain-style hash linking...")
    ledger = add_blockchain_style_linking()
    
    # 5. Verify blockchain integrity
    print("\n5. Verifying blockchain integrity...")
    verify_blockchain_integrity()
    
    # 6. Create summary report
    print("\n6. Creating summary report...")
    create_summary_report(report_files)
    
    print("\n" + "="*60)
    print("✅ Complete Report Generated")
    print("="*60)
    print("\nGenerated files:")
    for file in report_files:
        print(f"  - {file}")
    print("  - report_summary.txt")


def create_summary_report(report_files):
    """
    Create a text summary of all reports
    """
    # FIX: Added encoding='utf-8' to support the checkmark character (✓)
    with open(os.path.join("outputs", "reports", "report_summary.txt"), "w", encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("ELECTION RESULTS - COMPLETE REPORT\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Results summary
        try:
            with open(os.path.join("data", "election_results.json"), "r") as results_f:
                results = json.load(results_f)
            
            f.write("ELECTION RESULTS\n")
            f.write("-" * 60 + "\n")
            
            # FIX START: Using corrected keys for report summary
            total_votes = results.get('total_votes', 0)
            f.write(f"Total Votes: {total_votes}\n")
            f.write(f"Winner: Candidate {results.get('winner', 'N/A')}\n\n")
            
            f.write("Vote Distribution:\n")
            for candidate, count in results.get('vote_counts', {}).items():
                percentage = (count / total_votes * 100) if total_votes > 0 else 0
                f.write(f"  Candidate {candidate}: {count} votes ({percentage:.1f}%)\n")
            # FIX END
            
        except:
            f.write("Results not available\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("GENERATED FILES\n")
        f.write("="*60 + "\n\n")
        
        for file in report_files:
            f.write(f"  ✓ {file}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("SECURITY FEATURES\n")
        f.write("="*60 + "\n\n")
        f.write("  ✓ RSA-2048 Encryption\n")
        f.write("  ✓ Time-Lock Mechanism\n")
        f.write("  ✓ SHA-256 Integrity Hashing\n")
        f.write("  ✓ Blockchain-Style Linking\n")
        f.write("  ✓ One-Time Voting Enforcement\n")
        f.write("  ✓ Tamper-Evident Ledger\n")
    
    print("✅ Summary report created: report_summary.txt")


# ============ Main Execution ============

if __name__ == "__main__":
    generate_complete_report()