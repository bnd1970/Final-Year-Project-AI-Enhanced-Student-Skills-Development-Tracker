# auth.py
import pandas as pd
from pathlib import Path
import hashlib

USER_DIR = Path("user_inform")
USERS_FILE = USER_DIR / "users.xlsx"
GROUPS_FILE = USER_DIR / "groups.xlsx"

def init_user_dir():
    USER_DIR.mkdir(exist_ok=True)
    if not USERS_FILE.exists():
        pd.DataFrame(columns=["username", "password", "role", "group"]).to_excel(USERS_FILE, index=False)
    if not GROUPS_FILE.exists():
        pd.DataFrame(columns=["group_name", "creator"]).to_excel(GROUPS_FILE, index=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user():
    init_user_dir()
    print("\n=== 用户注册 ===")
    username = input("请输入用户名：").strip()
    
    users = pd.read_excel(USERS_FILE)
    if username in users['username'].values:
        print("用户名已存在！")
        return False

    password = hash_password(input("请输入密码："))
    role = input("请选择角色（组长/组员）：").strip()
    
    group = ""
    if role == "组长":
        group_name = input("请输入要创建的小组名称：").strip()
        groups = pd.read_excel(GROUPS_FILE)
        if group_name in groups['group_name'].values:
            print("小组名称已存在！")
            return False
        groups = pd.concat([groups, pd.DataFrame([{"group_name": group_name, "creator": username}])])
        groups.to_excel(GROUPS_FILE, index=False)
        group = group_name
    elif role == "组员":
        groups = pd.read_excel(GROUPS_FILE)
        if groups.empty:
            print("暂无可用小组，请先联系组长创建！")
            return False
        print("可用小组：")
        print(groups)
        group = input("请输入要加入的小组名称：").strip()
        if group not in groups['group_name'].values:
            print("无效的小组名称！")
            return False
    else:
        print("无效的角色！")
        return False

    new_user = pd.DataFrame([{
        "username": username,
        "password": password,
        "role": role,
        "group": group
    }])
    
    users = pd.concat([users, new_user])
    users.to_excel(USERS_FILE, index=False)
    print("注册成功！")
    return True

def login_user():
    init_user_dir()
    print("\n=== 用户登录 ===")
    username = input("用户名：").strip()
    password = hash_password(input("密码：").strip())
    
    users = pd.read_excel(USERS_FILE)
    user = users[(users['username'] == username) & (users['password'] == password)]
    
    if not user.empty:
        print(f"登录成功！角色：{user['role'].values[0]}")
        return user.iloc[0].to_dict()
    print("用户名或密码错误！")
    return None