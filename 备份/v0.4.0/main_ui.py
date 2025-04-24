# main ui
import os
import sys
import subprocess
from pathlib import Path
import pandas as pd
from auth import register_user, login_user
from auth import get_available_groups

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
        print("3. Exit Program")
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
            print("\nExiting system...")
            sys.exit(0)
        else:
            print("Invalid selection")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

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
    while True:
        clear_screen()
        print("=== Group Management ===")
        print("1. View members")
        print("2. Manage ID mapping")
        print("3. Return")
        choice = input("Enter choice (1-3): ")
        
        if choice == '1':
            from auth import get_available_groups  # 新增导入
            print(f"Current group: {user_info['group']}")
            print("\nMember List:")
            
            # 从数据库获取成员信息
            with get_connection() as conn:
                members = pd.read_sql('''
                    SELECT username, role 
                    FROM users 
                    WHERE group_name = ?
                ''', conn, params=(user_info['group'],))
                
            print(members.to_string(index=False))
            input("\nPress Enter to return...")
        elif choice == '2':
            from auth import update_user_mapping
            update_user_mapping(user_info['group'])  # 进入新界面
        elif choice == '3':
            break
        else:
            print("Invalid selection")
        input("\nPress Enter to continue...")

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
                    {'password_hash': hash_password(new_pw)}
                )
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
    from auth import get_connection  # 新增导入
    
    while True:
        clear_screen()
        print("=== Leader Operations ===")
        print("1. Transfer leadership")
        print("2. Leave group")
        print("3. Return")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            try:
                with get_connection() as conn:
                    # 从数据库获取成员列表
                    members = pd.read_sql('''
                        SELECT username, role 
                        FROM users 
                        WHERE group_name = ? 
                        AND username != ?
                    ''', conn, params=(user_info['group'], user_info['username']))
                    
                    if members.empty:
                        print("没有可转让权限的成员！")
                        input()
                        continue
                        
                    print("选择新组长:")
                    print(members.to_string(index=False))
                    new_leader = input("输入用户名: ").strip()
                    
                    # 验证用户名有效性
                    if new_leader not in members['username'].values:
                        print("无效的用户名！")
                        input()
                        continue
                        
                    # 执行权限转移
                    from auth import transfer_leadership
                    if transfer_leadership(user_info['username'], new_leader, user_info['group']):
                        print("组长权限已成功转移！")
                        user_info['role'] = 'member'
                        return
                    else:
                        print("权限转移失败！")
                    input()
            
            except sqlite3.Error as e:
                print(f"数据库错误: {str(e)}")
                input()
        
        elif choice == '2':
            try:
                with get_connection() as conn:
                    # 检查是否还有其他成员
                    count = conn.execute('''
                        SELECT COUNT(*) 
                        FROM users 
                        WHERE group_name = ?
                    ''', (user_info['group'],)).fetchone()[0]
                    
                    if count > 1:
                        print("转让组长权限后才能退出群组！")
                    else:
                        from auth import update_user_info
                        if update_user_info(user_info['username'], {'group_name': ''}):
                            print("已成功退出群组！")
                            user_info['group'] = ''
                        else:
                            print("退出群组失败！")
                    input()
            
            except sqlite3.Error as e:
                print(f"数据库错误: {str(e)}")
                input()
        
        elif choice == '3':
            break

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    main_menu()