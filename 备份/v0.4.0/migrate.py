import pandas as pd
import sqlite3
from pathlib import Path

# 修复路径配置
DB_DIR = Path("user_inform")
DB_PATH = DB_DIR / "system.db"

def migrate_users():
    try:
        DB_DIR.mkdir(exist_ok=True)  # 确保目录存在
        conn = sqlite3.connect(DB_PATH)
        
        # 创建表结构（与auth.py一致）
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT CHECK(role IN ('leader', 'member')) NOT NULL,
            group_name TEXT DEFAULT ''
        )''')
        
        # 迁移用户数据
        users_df = pd.read_excel("user_inform/users.xlsx")
        for _, row in users_df.iterrows():
            try:
                conn.execute('''INSERT INTO users 
                             (username, password_hash, role, group_name)
                             VALUES (?, ?, ?, ?)''',
                             (row['username'], row['password'], 
                              row['role'], row['group']))
            except sqlite3.IntegrityError:
                print(f"跳过重复用户: {row['username']}")
        
        conn.commit()
        print(f"成功迁移 {len(users_df)} 条用户数据")

    except Exception as e:
        print(f"用户迁移失败: {str(e)}")
    finally:
        if conn:
            conn.close()

def migrate_groups():
    try:
        DB_DIR.mkdir(exist_ok=True)  # 双重确认目录存在
        conn = sqlite3.connect(DB_PATH)
        
        # 创建表结构
        conn.execute('''CREATE TABLE IF NOT EXISTS groups (
            group_name TEXT PRIMARY KEY,
            creator TEXT NOT NULL
        )''')
        
        # 迁移群组数据
        groups_df = pd.read_excel("user_inform/groups.xlsx")
        for _, row in groups_df.iterrows():
            try:
                conn.execute('''INSERT INTO groups 
                             (group_name, creator)
                             VALUES (?, ?)''',
                             (row['group_name'], row['creator']))
            except sqlite3.IntegrityError:
                print(f"跳过重复群组: {row['group_name']}")
        
        conn.commit()
        print(f"成功迁移 {len(groups_df)} 条群组数据")

    except Exception as e:
        print(f"群组迁移失败: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_users()
    migrate_groups()
    print("\n迁移完成！数据库位置:", DB_PATH.resolve())