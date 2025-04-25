# main ui
import os
import sys
import subprocess
from pathlib import Path
import pandas as pd
from auth import register_user, login_user
from auth import USERS_FILE, GROUPS_FILE

INPUT_DIR = Path("input_form")
OUTPUT_DIR = Path("output_form")
USER_DIR = Path("user_inform")

def init_directories():
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    USER_DIR.mkdir(exist_ok=True)

def auth_module():
    while True:
        print("\n=== User Authentication ===")
        print("1. Login")
        print("2. Register")
        print("3. Back")
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            user = login_user()
            if user:
                return user
        elif choice == "2":
            if register_user():
                print("Registration successful!")
            else:
                print("Registration failed. Please try again.")
        elif choice == "3":
            return None
        else:
            print("Invalid selection")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def list_files(directory, extension=".xlsx"):
    return sorted([
        f.name for f in directory.glob(f"*{extension}") 
        if f.is_file() and not f.name.startswith('~$')  # Added filter condition
    ])

def select_file(files, prompt):
    print(prompt)
    for i, f in enumerate(files, 1):
        print(f"{i}. {f}")
    while True:
        try:
            choice = int(input("Enter selection number: "))
            return files[choice-1]
        except (ValueError, IndexError):
            print("Invalid input, please select again")

def preprocess_module():
    clear_screen()
    print("=== Preprocessing Module ===")
    
    input_files = list_files(INPUT_DIR)
    if not input_files:
        input("Input directory is empty, press Enter to return...")
        return
    
    selected = select_file(input_files, "Please select the raw file to process:")
    output_name = input("Enter output filename (without extension): ").strip() + ".xlsx"
    
    cmd = [
        sys.executable, "preprocess_form.py",
        str(INPUT_DIR/selected),
        str(OUTPUT_DIR/output_name)
    ]
    subprocess.run(cmd)
    input("\nProcessing complete, press Enter to return to main menu...")

def analysis_module():
    clear_screen()
    print("=== Analysis Module ===")
    
    output_files = list_files(OUTPUT_DIR)
    if not output_files:
        input("Output directory is empty, press Enter to return...")
        return
    
    selected = select_file(output_files, "Please select the file to analyze:")
    
    cmd = [
        sys.executable, "analysis_form.py",
        "--input", str(OUTPUT_DIR/selected)
    ]
    subprocess.run(cmd)
    input("\nAnalysis complete, press Enter to return to main menu...")

def main_menu():
    init_directories()
    while True:
        clear_screen()
        print("=== Team Collaboration Analysis System ===")
        user_info = auth_module()
        if not user_info:
            continue
            
        while True:
            clear_screen()
            role_display = "Leader" if user_info['role'] == "leader" else "Member"
            print(f"\nCurrent user: {user_info['username']} ({role_display})")
            print("=== Main Menu ===")
            print("1. Preprocess chat files")
            print("2. Analyze collaboration")
            if user_info['role'] == "leader":
                print("3. Manage groups")
            print("4. Profile settings")
            print("5. Logout")
            print("Type 'exit' to quit system")
            
            choice = input("Enter choice (1-5 or 'exit'): ").strip().lower()
            
            if choice == 'exit':
                print("Exiting system...")
                sys.exit()
            elif choice == "1":
                preprocess_module()
            elif choice == "2":
                analysis_module()
            elif choice == "3" and user_info['role'] == "leader":
                manage_group_module(user_info)
            elif choice == "4":
                profile_module(user_info)  # 新增的个人设置模块
            elif choice == "5":
                break
            else:
                input("Invalid choice. Press Enter to continue...")

def manage_group_module(user_info):
    clear_screen()
    print("=== Group Management ===")
    print("1. View members")
    print("2. Manage ID mapping")
    print("3. Return")
    choice = input("Enter choice (1-3): ")
    
    if choice == '1':
        groups = pd.read_excel(GROUPS_FILE, engine='openpyxl')
        print(f"Current group: {user_info['group']}")
        print("\nMember List:")
        users = pd.read_excel(USERS_FILE, engine='openpyxl')
        print(users[users['group'] == user_info['group']])
        input("\nPress Enter to return...")
    elif choice == '2':
        from auth import update_user_mapping
        update_user_mapping(user_info['group'])

def profile_module(user_info):
    while True:
        clear_screen()
        print("=== Profile Management ===")
        print(f"Username: {user_info['username']}")
        print(f"Role: {user_info['role'].capitalize()}")
        print(f"Group: {user_info['group']}")
        
        print("\n1. Change password")
        print("2. Manage group")
        print("3. Return to main menu")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            new_pw = input("Enter new password: ").strip()
            if new_pw:
                from auth import hash_password, update_user_info
                success = update_user_info(user_info['username'], 
                                      {'password': hash_password(new_pw)})
                print("Password updated!" if success else "Update failed!")
            input("Press Enter to continue...")
        
        elif choice == '2':
            if user_info['role'] == 'member':
                member_group_operations(user_info)
            else:
                leader_group_operations(user_info)
        
        elif choice == '3':
            break

def member_group_operations(user_info):
    """组员的小组操作"""
    from auth import get_available_groups, update_user_info
    
    while True:
        clear_screen()
        print("=== Group Operations ===")
        print("Current group:", user_info['group'])
        print("1. Join a group")
        print("2. Leave group")
        print("3. Return")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            groups = get_available_groups()
            if groups.empty:
                print("No available groups!")
                input()
                continue
                
            print("Available groups:")
            print(groups[['group_name', 'creator']].to_string(index=False))
            group_name = input("Enter group name to join: ").strip()
            
            if group_name in groups['group_name'].values:
                if update_user_info(user_info['username'], {'group': group_name}):
                    print("Successfully joined group!")
                    user_info['group'] = group_name
                else:
                    print("Failed to join group!")
            else:
                print("Invalid group name!")
            input()
        
        elif choice == '2':
            if update_user_info(user_info['username'], {'group': ''}):
                print("Left group successfully!")
                user_info['group'] = ''
            else:
                print("Failed to leave group!")
            input()
        
        elif choice == '3':
            break

def leader_group_operations(user_info):
    """组长的小组操作"""
    from auth import get_available_groups, transfer_leadership
    
    while True:
        clear_screen()
        print("=== Leader Operations ===")
        print("1. Transfer leadership")
        print("2. Leave group")
        print("3. Return")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            users = pd.read_excel(USERS_FILE, engine='openpyxl')
            members = users[(users['group'] == user_info['group']) & 
                          (users['username'] != user_info['username'])]
            
            if members.empty:
                print("No members available for transfer!")
                input()
                continue
                
            print("Select new leader:")
            print(members[['username', 'role']].to_string(index=False))
            new_leader = input("Enter username: ").strip()
            
            if new_leader in members['username'].values:
                if transfer_leadership(user_info['username'], new_leader, user_info['group']):
                    print("Leadership transferred!")
                    user_info['role'] = 'member'
                    return
                else:
                    print("Transfer failed!")
            else:
                print("Invalid username!")
            input()
        
        elif choice == '2':
            users = pd.read_excel(USERS_FILE, engine='openpyxl')
            if len(users[users['group'] == user_info['group']]) > 1:
                print("Cannot leave group without transferring leadership!")
            else:
                if update_user_info(user_info['username'], {'group': ''}):
                    print("Left group successfully!")
                    user_info['group'] = ''
                else:
                    print("Failed to leave group!")
            input()
        
        elif choice == '3':
            break

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    main_menu()