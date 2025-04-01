# main ui
import os
import sys
import subprocess
from pathlib import Path
import pandas as pd
from auth import register_user, login_user

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
            print(f"\nCurrent user: {user_info['username']} ({user_info['role']})")
            print("=== Main Menu ===")
            print("1. Preprocess chat files")
            print("2. Analyze collaboration")
            if user_info['role'] == "leader":
                print("3. Manage groups")
            print("4. Logout")
            
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == "1":
                preprocess_module()
            elif choice == "2":
                analysis_module()
            elif choice == "3" and user_info['role'] == "leader":
                manage_group_module(user_info)
            elif choice == "4":
                break
            else:
                input("Invalid choice. Press Enter to continue...")

def manage_group_module(user_info):
    clear_screen()
    print("=== Group Management ===")
    groups = pd.read_excel(GROUPS_FILE, engine='openpyxl')
    print(f"Current group: {user_info['group']}")
    print("\nMember List:")
    users = pd.read_excel(USERS_FILE, engine='openpyxl')
    print(users[users['group'] == user_info['group']])
    input("\nPress Enter to return...")

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    main_menu()