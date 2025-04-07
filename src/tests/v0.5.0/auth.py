# auth.py
import sys
import os
import sqlite3
import hashlib
import pandas as pd
from pathlib import Path
from database import init_db

# 数据库配置
DB_PATH = Path("user_inform") / "system.db"

def get_connection():
    """统一数据库连接入口"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")  # 启用外键约束
    return conn

def hash_password(password: str) -> str:
    # 使用 SHA-256 哈希算法
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
            
            if role == "leader":
                group_name = input("Enter new group name: ").strip()
                if not group_name:
                    print("Group name cannot be empty!")
                    return False

                # 检查群组是否已存在
                if conn.execute("SELECT 1 FROM groups WHERE group_name=?", (group_name,)).fetchone():
                    print("Group name already exists!")
                    return False

                # 先插入用户记录，确保外键引用有效
                try:
                    conn.execute('''
                        INSERT INTO users 
                        (username, password_hash, role, group_name)
                        VALUES (?, ?, ?, ?)
                    ''', (username, password_hash, role, group_name))
                except sqlite3.Error as e:
                    print(f"Failed to insert user: {str(e)}")
                    return False

                # 再插入群组记录
                try:
                    conn.execute("INSERT INTO groups (group_name, creator) VALUES (?, ?)", 
                                 (group_name, username))
                except sqlite3.Error as e:
                    print(f"Failed to create group: {str(e)}")
                    conn.rollback()
                    return False

            elif role == "member":
                groups = get_available_groups()
                if groups.empty:
                    print("No available groups. Please ask a leader to create one first.")
                    return False
                    
                print("\nAvailable Groups:")
                print(groups.to_string(index=False))
                group_name = input("Enter group name to join: ").strip()
                if not conn.execute("SELECT 1 FROM groups WHERE group_name=?", (group_name,)).fetchone():
                    print("Invalid group name!")
                    return False

                # 插入用户记录
                try:
                    conn.execute('''
                        INSERT INTO users 
                        (username, password_hash, role, group_name)
                        VALUES (?, ?, ?, ?)
                    ''', (username, password_hash, role, group_name))
                except sqlite3.Error as e:
                    print(f"Failed to insert user: {str(e)}")
                    conn.rollback()
                    return False

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

def enhanced_process_mapping(group_name: str, file_path: Path):
    """增强版批量导入（支持混合模式）"""
    clear_screen()
    print(f"\n=== 智能批量导入 (文件: {file_path.name}) ===")
    
    try:
        original_ids = get_original_ids(file_path)
        if not original_ids:
            print("错误：文件中未找到有效的原始ID")
            return

        print("文件中的原始ID列表:")
        for i, oid in enumerate(original_ids, 1):
            print(f"{i}. {oid}")

        print("\n请选择映射模式:")
        print("1. 全自动映射（原始ID直接作为系统ID）")
        print("2. 全手动映射（为每个ID指定系统ID）")
        print("3. 混合模式（自由选择部分ID映射）")
        mode = input("请输入选项 (1/2/3): ").strip()

        success_count = 0
        with get_connection() as conn:
            for idx, original_id in enumerate(original_ids, 1):
                # 混合模式逻辑
                if mode == '3':
                    print(f"\n当前处理 ({idx}/{len(original_ids)}): {original_id}")
                    action = input("是否手动映射？(y=手动/n=自动/q=退出): ").lower()
                    if action == 'q':
                        break
                    elif action == 'y':
                        system_id = input(f"请输入系统ID: ").strip()
                        if not system_id:
                            print("跳过该ID")
                            continue
                    else:
                        system_id = original_id  # 自动模式
                else:
                    system_id = original_id if mode == '1' else input(f"请输入'{original_id}'的系统ID: ")

                # 验证系统ID有效性
                if not check_user_exists(system_id):
                    print(f"错误：系统ID '{system_id}' 未注册")
                    continue

                # 写入数据库
                try:
                    conn.execute('''
                        INSERT INTO id_mappings (original_id, system_id, group_name)
                        VALUES (?, ?, ?)
                        ON CONFLICT(original_id, group_name) 
                        DO UPDATE SET system_id = excluded.system_id
                    ''', (original_id, system_id, group_name))
                    success_count += 1
                except sqlite3.Error as e:
                    print(f"保存失败: {original_id} → {system_id} ({str(e)})")

            conn.commit()
            print(f"\n成功导入 {success_count}/{len(original_ids)} 条映射关系")

    except Exception as e:
        print(f"导入失败: {str(e)}")
    
    input("\n按回车继续...")

def update_user_mapping(group_name):
    """ID映射管理界面（不再强制选择文件）"""
    clear_screen()
    print(f"\n=== ID映射管理（群组：{group_name}） ===")
    
    while True:
        print("\n请选择操作：")
        print("1. 查看当前映射")
        print("2. 手动添加/修改映射")
        print("3. 删除映射")
        print("4. 从文件批量导入")
        print("5. 返回群组管理")
        
        choice = input("请输入选项 (1-5): ").strip()
        
        if choice == '1':
            view_mappings(group_name)
        elif choice == '2':
            manual_edit_mapping(group_name)
        elif choice == '3':
            delete_mapping(group_name)
        elif choice == '4':
            # 仅在选择批量导入时要求文件
            chat_file = select_output_file()
            if chat_file:
                enhanced_process_mapping(group_name, chat_file)  # 调用增强版函数
        elif choice == '5':
            break
        else:
            print("无效输入")
        input("\n按回车继续...")

def manual_edit_mapping(group_name):

        print(f"\n=== 手动编辑映射 (群组: {group_name}) ===")
        
        # 步骤1: 获取用户输入
        original_id = input("请输入聊天记录中的原始ID (输入q退出): ").strip()
        if original_id.lower() == 'q':
            return
        
        system_id = input("请输入对应的系统注册ID: ").strip()
        if not system_id:
            print("错误：系统ID不能为空！")
            input("按回车继续...")
            return
        
        # 步骤2: 验证系统ID有效性
        if not check_user_exists(system_id):
            print(f"错误：系统ID '{system_id}' 未注册！")
            input("按回车继续...")
            return
        
        # 步骤3: 执行数据库操作
        try:
            with get_connection() as conn:
                # 使用UPSERT语法处理重复键
                conn.execute('''
                    INSERT INTO id_mappings (original_id, system_id, group_name)
                    VALUES (?, ?, ?)
                    ON CONFLICT(original_id, group_name) 
                    DO UPDATE SET system_id = excluded.system_id
                ''', (original_id, system_id, group_name))
                
                # 同步更新Excel映射文件（可选）
                update_excel_mapping(
                    group_name=group_name,
                    original_id=original_id,
                    system_id=system_id
                )
                
                conn.commit()
                print(f"成功保存映射关系：{original_id} → {system_id}")
                
        except sqlite3.Error as e:
            print(f"数据库操作失败: {str(e)}")
            if "FOREIGN KEY constraint failed" in str(e):
                print("提示：请确保输入的system_id已存在于用户表")
        except Exception as e:
            print(f"未知错误: {str(e)}")
        
        input("按回车继续...")
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
    """验证用户是否存在于数据库"""
    try:
        with get_connection() as conn:
            return conn.execute(
                "SELECT 1 FROM users WHERE username = ?", 
                (username,)
            ).fetchone() is not None
    except sqlite3.Error:
        return False

def update_excel_mapping(group_name: str, original_id: str, system_id: str):
    """同步更新Excel映射文件（保持兼容性）"""
    try:
        mapping_path = Path("user_inform/user_mapping.xlsx")
        
        # 读取现有数据
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
    except Exception as e:
        print(f"警告：Excel映射文件更新失败（不影响数据库操作）: {str(e)}")

def process_file_mapping(group_name: str, file_path: Path):
    """从预处理文件批量导入映射关系"""
    clear_screen()
    print(f"\n=== 批量导入映射 (文件: {file_path.name}) ===")
    
    try:
        # 读取文件获取原始ID列表
        original_ids = get_original_ids(file_path)
        if not original_ids:
            print("错误：文件中未找到有效的原始ID")
            return

        # 显示可用原始ID并选择映射方式
        print("文件中的原始ID列表:")
        for i, oid in enumerate(original_ids, 1):
            print(f"{i}. {oid}")

        # 选择映射模式
        print("\n请选择映射方式:")
        print("1. 自动映射（原始ID直接作为系统ID）")
        print("2. 手动为每个原始ID指定系统ID")
        mode = input("请输入选项 (1/2): ").strip()

        # 执行映射
        success_count = 0
        with get_connection() as conn:
            for original_id in original_ids:
                if mode == '1':
                    system_id = original_id  # 自动映射
                else:
                    system_id = input(f"请输入原始ID '{original_id}' 对应的系统ID: ").strip()
                    if not system_id:
                        print(f"跳过 {original_id}")
                        continue

                # 验证系统ID有效性
                if not check_user_exists(system_id):
                    print(f"错误：系统ID '{system_id}' 未注册")
                    continue

                # 写入数据库
                try:
                    conn.execute('''
                        INSERT INTO id_mappings (original_id, system_id, group_name)
                        VALUES (?, ?, ?)
                        ON CONFLICT(original_id, group_name) 
                        DO UPDATE SET system_id = excluded.system_id
                    ''', (original_id, system_id, group_name))
                    success_count += 1
                except sqlite3.Error as e:
                    print(f"保存失败: {original_id} → {system_id} ({str(e)})")

            conn.commit()
            print(f"\n成功导入 {success_count}/{len(original_ids)} 条映射关系")

    except Exception as e:
        print(f"批量导入失败: {str(e)}")
    
    input("\n按回车继续...")

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

def view_mappings(group_name: str):
    try:
        with get_connection() as conn:
            df = pd.read_sql('''
                SELECT original_id, system_id 
                FROM id_mappings 
                WHERE group_name = ?
            ''', conn, params=(group_name,))
            
            if df.empty:
                print("当前没有映射记录")
                return
                
            print("\n当前映射关系：")
            print(df.to_string(index=False))
    except Exception as e:
        print(f"映射查询失败: {str(e)}")
    """添加/修改映射"""
    original_id = input("输入原始ID（聊天记录中的ID）: ").strip()
    system_id = input("输入系统注册ID: ").strip()
    
    # 验证系统ID有效性
    if not conn.execute("SELECT 1 FROM users WHERE username=?", (system_id,)).fetchone():
        print("错误：该用户未注册！")
        return
    
    try:
        # 使用UPSERT语法
        conn.execute('''
            INSERT INTO id_mappings (original_id, system_id, group_name)
            VALUES (?, ?, ?)
            ON CONFLICT(original_id, group_name) 
            DO UPDATE SET system_id = excluded.system_id
        ''', (original_id, system_id, group_name))
        
        conn.commit()
        print("映射关系已保存！")
    except sqlite3.Error as e:
        print(f"保存失败: {str(e)}")
        conn.rollback()
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

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    init_db()