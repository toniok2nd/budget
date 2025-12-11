import requests
import sys

BASE_URL = "https://localhost"
CERT = ("certs/client.crt", "certs/client.key")
VERIFY = False 

s = requests.Session()
s.cert = CERT
s.verify = VERIFY

def login(username, password):
    print(f"Logging in {username}...")
    try:
        resp = s.post(f"{BASE_URL}/login", data={"username": username, "password": password}, allow_redirects=True)
        if resp.status_code == 200 and "My Budget" in resp.text:
            return True
        print(f"Login failed: {resp.status_code}")
        print(resp.text[:500])
        return False
    except Exception as e:
        print(f"Connection error: {e}")
        return False

def verify_expense_deletion():
    # 1. Add Transaction (implied expense)
    print("Adding transaction...")
    data = {"amount": "100.00", "description": "TestDelete", "category": "1"} # Food
    # 'type' is no longer sent, backend defaults to 'expense'
    
    resp = s.post(f"{BASE_URL}/add", data=data, allow_redirects=True)
    if "TestDelete" not in resp.text:
        print("FAILED: Transaction not found in dashboard/history immediately after add")
        # Depending on redirect, might be in index or need to go history
    
    # Check history to find ID
    print("Checking history to find ID...")
    resp = s.get(f"{BASE_URL}/history")
    if "TestDelete" not in resp.text:
        print("FAILED: Transaction not found in history")
        return False
        
    # Extract ID (simple find, assumes TestDelete is unique/recent)
    # We look for /transactions/<id>/delete
    try:
        # Find the link associated with TestDelete. 
        # Structure: ...TestDelete... <a href="/transactions/X/delete" ...
        part = resp.text.split("TestDelete")[1]
        link_part = part.split('href="/transactions/')[1]
        tx_id = link_part.split('/delete')[0]
        print(f"Found Transaction ID: {tx_id}")
    except IndexError:
        print("FAILED: Could not parse Transaction ID from history page")
        return False

    # 2. Delete Transaction
    print(f"Deleting transaction {tx_id}...")
    resp = s.get(f"{BASE_URL}/transactions/{tx_id}/delete", allow_redirects=True)
    
    if resp.status_code == 200:
        if "Transaction deleted" in resp.text:
            print("Verified: Flash message 'Transaction deleted' found")
        
        # Verify it's gone
        if f"/transactions/{tx_id}/delete" not in resp.text:
             print("Verified: Link gone from history")
             return True
        else:
             print("FAILED: Transaction delete link still present in history")
             return False
    else:
        print(f"Delete failed with code {resp.status_code}")
        return False

if __name__ == "__main__":
    if login("admin", "admin"):
        if verify_expense_deletion():
            print("SUCCESS: Expense mode and deletion verified.")
            sys.exit(0)
    print("FAILURE: Verification failed.")
    sys.exit(1)
