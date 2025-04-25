# auth.py
import sqlite3
import hashlib
import sys
from pathlib import Path
import pandas as pd

# 数据库配置
DB_PATH = Path("user_inform") / "system.db"

def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)

def init_db():
    """初始化数据库表结构"""
    try:
        Path("user_inform").mkdir(exist_ok=True)
        with get_connection() as conn:
            c = conn.cursor()
            
            # 用户表
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT CHECK(role IN ('leader', 'member')) NOT NULL,
                group_name TEXT DEFAULT ''
            )''')
            
            # 群组表
            c.execute('''CREATE TABLE IF NOT EXISTS groups (
                group_name TEXT PRIMARY KEY,
                creator TEXT NOT NULL,
                FOREIGN KEY(creator) REFERENCES users(username)
            )''')
            
            conn.commit()
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")
        sys.exit(1)

def hash_password(password: str) -> str:
    """密码哈希处理"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user() -> bool:
    """用户注册功能"""
    init_db()
    print("\n=== User Registration ===")
    
    try:
        username = input("Enter username: ").strip()
        if not username:
            print("Username cannot be empty!")
            return False

        with get_connection() as conn:
            # 检查用户名唯一性
            if conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
                print("Username already exists!")
                return False

            # 密码处理
            password = input("Enter password: ").strip()
            if not password:
                print("Password cannot be empty!")
                return False
            password_hash = hash_password(password)

            # 角色选择
            print("Select role:")
            print("1. Leader (can create groups)")
            print("2. Member (join existing groups)")
            role_choice = input("Enter choice (1-2): ").strip()
            
            if role_choice not in ['1', '2']:
                print("Invalid role selection!")
                return False
            
            role = "leader" if role_choice == '1' else "member"
            group_name = ""

            # 组长创建群组逻辑
            if role == "leader":
                group_name = input("Enter new group name: ").strip()
                if not group_name:
                    print("Group name cannot be empty!")
                    return False
                    
                try:
                    conn.execute("INSERT INTO groups VALUES (?, ?)", 
                                (group_name, username))
                except sqlite3.IntegrityError:
                    print("Group name already exists!")
                    return False

            # 成员加入群组逻辑
            elif role == "member":
                groups = get_available_groups()
                if groups.empty:
                    print("No available groups. Please ask a leader to create one first.")
                    return False
                    
                print("\nAvailable Groups:")
                print(groups.to_string(index=False))
                group_name = input("Enter group name to join: ").strip()
                
                if not conn.execute("SELECT 1 FROM groups WHERE group_name=?", 
                                  (group_name,)).fetchone():
                    print("Invalid group name!")
                    return False

            # 插入用户记录
            conn.execute('''INSERT INTO users 
                         (username, password_hash, role, group_name)
                         VALUES (?, ?, ?, ?)''',
                         (username, password_hash, role, group_name))
            conn.commit()
            print("Registration successful!")
            return True

    except sqlite3.Error as e:
        print(f"Registration failed: {str(e)}")
        return False

def login_user() -> dict:
    """用户登录功能"""
    init_db()
    print("\n=== User Login ===")
    
    try:
        username = input("Username: ").strip()
        password = hash_password(input("Password: ").strip())
        
        with get_connection() as conn:
            user = conn.execute('''SELECT username, role, group_name 
                                FROM users 
                                WHERE username=? AND password_hash=?''',
                              (username, password)).fetchone()
            
            if user:
                print(f"Login successful! Role: {user[1]}")
                return {
                    "username": user[0],
                    "role": user[1],
                    "group": user[2]
                }
            print("Invalid username or password!")
            return None
            
    except sqlite3.Error as e:
        print(f"Login error: {str(e)}")
        return None

def update_user_info(username: str, update_data: dict) -> bool:
    try:
        with get_connection() as conn:
            # 构建更新语句
            set_clause = ", ".join([f"{k}=?" for k in update_data.keys()])
            values = list(update_data.values())
            values.append(username)
            
            conn.execute(f'''UPDATE users 
                           SET {set_clause}
                           WHERE username=?''', values)
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"Update failed: {str(e)}")
        return False

def get_available_groups() -> pd.DataFrame:
    """获取可用群组列表"""
    try:
        with get_connection() as conn:
            return pd.read_sql("SELECT group_name, creator FROM groups", conn)
    except sqlite3.Error:
        return pd.DataFrame(columns=["group_name", "creator"])

def transfer_leadership(old_leader: str, new_leader: str, group_name: str) -> bool:
    """转让组长权限"""
    try:
        with get_connection() as conn:
            # 开启事务
            conn.execute("BEGIN TRANSACTION")
            
            # 更新用户角色
            conn.execute('''UPDATE users SET role='member' 
                          WHERE username=?''', (old_leader,))
            conn.execute('''UPDATE users SET role='leader' 
                          WHERE username=?''', (new_leader,))
            
            # 更新群组创建者
            conn.execute('''UPDATE groups SET creator=? 
                          WHERE group_name=?''', (new_leader, group_name))
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Leadership transfer failed: {str(e)}")
        return False
    
def select_output_file():
    """选择预处理后的聊天文件"""
    output_dir = Path("output_form")
    files = [f for f in output_dir.glob("*.xlsx") if f.is_file()]
    
    print("\n可用的预处理文件：")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f.name}")
    
    while True:
        try:
            choice = int(input("请选择文件编号："))
            selected = files[choice-1]
            return selected
        except (ValueError, IndexError):
            print("输入无效，请重新选择")

def get_original_ids(file_path):
    """从指定文件获取原始ID列表"""
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        return df['talker'].unique().tolist()
    except Exception as e:
        print(f"读取文件失败：{str(e)}")
        return []

def init_mapping_file():
    mapping_path = Path("user_inform/user_mapping.xlsx")
    if not mapping_path.exists():
        pd.DataFrame(columns=['group', 'original_id', 'system_id']).to_excel(
            mapping_path, index=False, engine='openpyxl')

def update_user_mapping(group_name):
    """ID映射管理界面"""
    init_mapping_file()
    
    # 选择聊天文件（增加临时文件过滤）
    chat_file = select_output_file()
    if not chat_file:
        return
    
    # 获取原始ID列表（增加异常处理）
    try:
        original_ids = get_original_ids(chat_file)
    except Exception as e:
        print(f"获取原始ID失败：{str(e)}")
        return

    while True:
        print(f"\n=== ID映射管理（群组：{group_name}） ===")
        print(f"当前文件：{chat_file.name}")
        print("1. 查看当前映射")
        print("2. 添加/修改映射")
        print("3. 删除映射")
        print("4. 更换文件")
        print("5. 返回群组管理")
        
        choice = input("请选择操作 (1-5): ").strip()
        
        if choice == '1':
            view_mappings(group_name)
        elif choice == '2':
            # 修复方法调用方式
            show_id_selection(original_ids, group_name)  # 移除self.
        elif choice == '3':
            delete_mapping(group_name)
        elif choice == '4':
            new_file = select_output_file()
            if new_file:
                chat_file = new_file
                original_ids = get_original_ids(chat_file)
        elif choice == '5':
            break
        else:
            print("无效选择")
        input("\n按回车继续...")

def show_id_selection(original_ids, group_name): 
    """显示原始ID选择界面"""
    print("\n可用的原始ID列表：")
    for i, oid in enumerate(original_ids, 1):
        print(f"{i}. {oid}")
    
    while True:
        try:
            choice = int(input("请选择要映射的ID编号（0返回）："))
            if choice == 0:
                return
            original_id = original_ids[choice-1]
            break
        except (ValueError, IndexError):
            print("输入无效")
    
    # 获取系统ID
    system_id = input("输入对应的系统注册ID：").strip()
    
    # 验证系统ID有效性（使用独立函数）
    if not check_user_exists(system_id):
        print("该用户ID未注册！")
        return
    
    # 保存映射（使用独立函数）
    save_mapping(group_name, original_id, system_id)

def check_user_exists(username: str) -> bool:
    """检查用户是否存在"""
    with get_connection() as conn:
        return conn.execute(
            "SELECT 1 FROM users WHERE username=?", 
            (username,)
        ).fetchone() is not None

def select_output_file():
    """选择预处理文件（增加临时文件过滤）"""
    output_dir = Path("output_form")
    files = [
        f for f in output_dir.glob("*.xlsx") 
        if f.is_file() and not f.name.startswith('~$')
    ]
    
    if not files:
        print("没有可用的预处理文件")
        return None
    
    print("\n可用的预处理文件：")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f.name}")
    
    while True:
        try:
            choice = int(input("请选择文件编号："))
            selected = files[choice-1]
            return selected
        except (ValueError, IndexError):
            print("输入无效，请重新选择")

def edit_mapping(group_name):
    """添加/修改映射关系"""
    while True:
        original_id = input("输入聊天记录中的原始ID（输入q退出）: ").strip()
        if original_id.lower() == 'q':
            break
            
        # 检查系统ID是否存在
        with get_connection() as conn:
            system_id = conn.execute(
                "SELECT username FROM users WHERE username=?",
                (original_id,)
            ).fetchone()
        
        if system_id:
            print(f"系统ID已存在: {system_id[0]}")
            continue
            
        # 手动映射
        new_id = input("输入要关联的系统注册ID: ").strip()
        if not new_id:
            print("系统ID不能为空！")
            continue
            
        # 保存到Excel
        df = pd.read_excel("user_inform/user_mapping.xlsx", engine='openpyxl')
        df = df[~(df['original_id'].eq(original_id) & df['group'].eq(group_name))]
        new_entry = pd.DataFrame([{
            'group': group_name,
            'original_id': original_id,
            'system_id': new_id
        }])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_excel("user_inform/user_mapping.xlsx", index=False, engine='openpyxl')
        print("映射已保存！")

def view_mappings(group_name):
    try:
        df = pd.read_excel("user_inform/user_mapping.xlsx")
        group_mappings = df[df['group'] == group_name]
        print("\nCurrent ID Mappings:")
        print(group_mappings.to_string(index=False))
    except FileNotFoundError:
        print("No mappings exist yet")

def add_mapping(group_name):
    original_id = input("Enter original ID: ").strip()
    system_id = input("Enter system ID: ").strip()
    
    try:
        df = pd.read_excel("user_inform/user_mapping.xlsx")
    except FileNotFoundError:
        df = pd.DataFrame(columns=['group', 'original_id', 'system_id'])
    
    new_entry = pd.DataFrame([{
        'group': group_name,
        'original_id': original_id,
        'system_id': system_id
    }])
    
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_excel("user_inform/user_mapping.xlsx", index=False)
    print("Mapping added successfully!")

def delete_mapping(group_name):
    original_id = input("Enter original ID to delete: ").strip()
    
    try:
        df = pd.read_excel("user_inform/user_mapping.xlsx")
        filtered = df[~((df['group'] == group_name) & (df['original_id'] == original_id))]
        
        if len(filtered) == len(df):
            print("No matching ID found")
        else:
            filtered.to_excel("user_inform/user_mapping.xlsx", index=False)
            print("Mapping deleted successfully")
    except FileNotFoundError:
        print("No mappings exist yet")

def save_mapping(group_name, original_id, system_id):
    """保存映射关系到Excel"""
    try:
        # 确保映射文件存在
        mapping_path = Path("user_inform/user_mapping.xlsx")
        mapping_path.parent.mkdir(exist_ok=True)
        
        if mapping_path.exists():
            df = pd.read_excel(mapping_path, engine='openpyxl')
        else:
            df = pd.DataFrame(columns=['group', 'original_id', 'system_id'])

        # 删除旧记录
        mask = (df['group'] == group_name) & (df['original_id'] == original_id)
        df = df[~mask]

        # 添加新记录
        new_row = pd.DataFrame([{
            'group': group_name,
            'original_id': original_id,
            'system_id': system_id
        }])
        df = pd.concat([df, new_row], ignore_index=True)

        # 保存文件
        df.to_excel(mapping_path, index=False, engine='openpyxl')
        print("映射关系保存成功！")
        
    except Exception as e:
        print(f"保存失败：{str(e)}")

if __name__ == "__main__":
    init_db()