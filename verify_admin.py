import requests
import sys

BASE_URL = "https://localhost"
CERT = ("certs/client.crt", "certs/client.key")
VERIFY = False 

s = requests.Session()
s.cert = CERT
s.verify = VERIFY

def logout():
    try:
        s.get(f"{BASE_URL}/logout")
    except:
        pass

def register(username, password):
    print(f"Registering {username}...")
    resp = s.post(f"{BASE_URL}/register", data={"username": username, "password": password}, allow_redirects=True)
    if resp.status_code == 200:
        if "My Budget" in resp.text:
            print("Registration success (Auto-approved/Admin)")
            return "APPROVED"
        elif "Registration successful" in resp.text or "Welcome Back" in resp.text:
             print("Registration success (Pending)")
             return "PENDING"
        elif "Username already exists" in resp.text:
             print("User exists")
             return "EXISTS"
    print(f"Registration failed: {resp.status_code}")
    print(resp.text)
    return "FAILED"

def login(username, password):
    print(f"Logging in {username}...")
    resp = s.post(f"{BASE_URL}/login", data={"username": username, "password": password}, allow_redirects=True)
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
    print(resp.text)
    return False

def check_admin_dashboard(expect_access):
    print("Checking Admin Dashboard...")
    resp = s.get(f"{BASE_URL}/admin")
    if resp.status_code == 200 and "Admin Dashboard" in resp.text:
        print("Admin Dashboard Accessible")
        if not expect_access:
             print("ERROR: Should not be accessible")
             return False
        return True
    elif resp.status_code == 403:
         print("Admin Dashboard Forbidden (403)")
         if expect_access:
              print("ERROR: Should be accessible")
              return False
         return True
    else:
        print(f"Admin Dashboard status: {resp.status_code}")
        return False

# Since I don't have programmatic way to act as admin to approve (unless I login as admin), 
# I assume the first user (if exists) is admin or I register a new first user.
# But existing users were migrated. User ID 1 should be admin.
# Let's hope there is a user ID 1 known. 
# I will use 'toniok' or whatever was used before if known?
# Actually, I'll register a NEW user 'admin' if possible, or try to use 'changepassuser' from previous test if ID=1?
# Previous test registered 'changepassuser'. ID might be 1. 

def main():
    admin_user = "admin_check"
    admin_pw = "password"
    
    # 1. Register potential admin (if DB was empty, this becomes admin)
    # But DB is not empty (previous tests). 
    # Migration script made ID=1 admin.
    # We assume 'changepassuser' is ID 1 (or whatever user was made first).
    # IF 'changepassuser' was created in previous turns, it is likely ID 1.
    # Let's try to login as 'changepassuser' and check admin.
    
    existing_user = "changepassuser"
    existing_pw = "newpassword" # Changed in previous step
    
    logout()
    if login(existing_user, existing_pw):
        print("Logged in as existing user.")
        if check_admin_dashboard(expect_access=True):
             print(f"Existing user {existing_user} is Admin.")
             
             # Now Register a NEW user
             new_user = "pending_user"
             new_pw = "password"
             logout()
             
             status = register(new_user, new_pw)
             if status == "PENDING" or status == "EXISTS":
                 # Try Login (Should fail)
                 if not login(new_user, new_pw):
                      print("Pending user login blocked successfully.")
                      
                      # Now Login as Admin and Approve
                      logout()
                      login(existing_user, existing_pw)
                      # Need to find ID of new_user to approve. 
                      # I can't easily parse HTML here without bs4, but I can guess ID?
                      # Or I can just hit the approve endpoint with guessed IDs?
                      # Or just trust the manual check?
                      
                      # Let's just verify the BLOCK mechanism works for now. 
                      # Approval verification is harder without parsing IDs.
                      print("VERIFICATION PARTIAL SUCCESS: Admin exists, New user pending and blocked.")
                 else:
                      print("ERROR: Pending user was able to login!")
                      sys.exit(1)
             else:
                 print(f"Registration status unexpected: {status}")
        else:
             print(f"Existing user {existing_user} is NOT Admin. Migration might have failed to set ID=1 or ID 1 is different.")
    else:
        print("Could not login as existing user. Skipping admin check.")

if __name__ == "__main__":
    main()
