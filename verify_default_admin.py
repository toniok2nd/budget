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
    except requests.exceptions.ConnectionError:
        print("Connection failed. Service might not be ready.")
        return False
        
    if resp.status_code == 200:
        if "My Budget" in resp.text:
            print("Login success")
            return True
        elif "Account pending approval" in resp.text:
            print("Login failed (Pending Approval detected)")
            return False
        elif "Invalid username or password" in resp.text:
            print("Login failed (Invalid credentials)")
            return False
    print(f"Login outcome unclear: {resp.status_code}")
    # print(resp.text)
    return False

def check_admin_dashboard():
    print("Checking Admin Dashboard...")
    resp = s.get(f"{BASE_URL}/admin")
    if resp.status_code == 200 and "Admin Dashboard" in resp.text:
        print("Admin Dashboard Accessible")
        return True
    else:
        print(f"Admin Dashboard status: {resp.status_code}")
        return False

if __name__ == "__main__":
    if login("admin", "admin"):
        if check_admin_dashboard():
            print("SUCCESS: Default admin login and dashboard access verified!")
            sys.exit(0)
    print("FAILURE: Default admin check failed.")
    sys.exit(1)
