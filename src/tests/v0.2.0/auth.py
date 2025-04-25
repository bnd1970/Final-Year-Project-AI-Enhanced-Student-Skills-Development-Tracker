# auth.py
import pandas as pd
from pathlib import Path
import hashlib
import sys

USER_DIR = Path("user_inform")
USERS_FILE = USER_DIR / "users.xlsx"
GROUPS_FILE = USER_DIR / "groups.xlsx"

ROLES = {
    1: "leader",
    2: "member"
}

def init_user_dir():
    try:
        USER_DIR.mkdir(exist_ok=True)
        
        if not USERS_FILE.exists():
            pd.DataFrame(columns=["username", "password", "role", "group"]).to_excel(
                USERS_FILE, index=False, engine='openpyxl'
            )
            
        if not GROUPS_FILE.exists():
            pd.DataFrame(columns=["group_name", "creator"]).to_excel(
                GROUPS_FILE, index=False, engine='openpyxl'
            )
    except Exception as e:
        print(f"Initialization failed: {str(e)}")
        sys.exit(1)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user():
    init_user_dir()
    print("\n=== User Registration ===")
    
    try:
        users = pd.read_excel(USERS_FILE, engine='openpyxl')
    except FileNotFoundError:
        users = pd.DataFrame(columns=["username", "password", "role", "group"])
    
    username = input("Enter username: ").strip()
    
    if not username:
        print("Username cannot be empty!")
        return False

    if not users.empty and username in users['username'].values:
        print("Username already exists!")
        return False

    password = hash_password(input("Enter password: ").strip())
    if not password:
        print("Password cannot be empty!")
        return False

    print("Select role:")
    print("1. Leader (can create groups)")
    print("2. Member (join existing groups)")
    role_choice = input("Enter choice (1-2): ").strip()
    
    if role_choice not in ['1', '2']:
        print("Invalid role selection!")
        return False
    
    role = ROLES[int(role_choice)]
    group = ""

    if role == "leader":
        try:
            groups = pd.read_excel(GROUPS_FILE, engine='openpyxl')
        except FileNotFoundError:
            groups = pd.DataFrame(columns=["group_name", "creator"])
        
        group_name = input("Enter new group name: ").strip()
        if not group_name:
            print("Group name cannot be empty!")
            return False
            
        if not groups.empty and group_name in groups['group_name'].values:
            print("Group name already exists!")
            return False
            
        new_group = pd.DataFrame([{"group_name": group_name, "creator": username}])
        groups = pd.concat([groups, new_group], ignore_index=True)
        groups.to_excel(GROUPS_FILE, index=False, engine='openpyxl')
        group = group_name
    elif role == "member":
        try:
            groups = pd.read_excel(GROUPS_FILE, engine='openpyxl')
        except FileNotFoundError:
            groups = pd.DataFrame(columns=["group_name", "creator"])
            
        if groups.empty:
            print("No available groups. Please ask a leader to create one first.")
            return False
            
        print("\nAvailable Groups:")
        print(groups[['group_name', 'creator']].to_string(index=False))
        group = input("Enter group name to join: ").strip()
        
        if group not in groups['group_name'].values:
            print("Invalid group name!")
            return False

    new_user = pd.DataFrame([{
        "username": username,
        "password": password,
        "role": role,
        "group": group
    }])
    
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_excel(USERS_FILE, index=False, engine='openpyxl')
    print("Registration successful!")
    return True

def login_user():
    init_user_dir()
    print("\n=== User Login ===")
    
    try:
        users = pd.read_excel(USERS_FILE, engine='openpyxl')
    except FileNotFoundError:
        print("No registered users yet")
        return None
    
    username = input("Username: ").strip()
    password = hash_password(input("Password: ").strip())
    
    user = users[(users['username'] == username) & (users['password'] == password)]
    
    if not user.empty:
        print(f"Login successful! Role: {user['role'].values[0]}")
        return user.iloc[0].to_dict()
    print("Invalid username or password!")
    return None