# database.py
import sqlite3
from pathlib import Path
import sys

# 统一数据库路径为 user_inform/system.db
DB_PATH = Path("user_inform") / "system.db"  # 修改路径

def init_db():
    """初始化数据库表结构（包含 id_mappings 表）"""
    try:
        Path("user_inform").mkdir(exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 用户表
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT CHECK(role IN ('leader', 'member')) NOT NULL,
                    group_name TEXT DEFAULT '')''')

        # 群组表
        c.execute('''CREATE TABLE IF NOT EXISTS groups
                    (group_name TEXT PRIMARY KEY,
                    creator TEXT NOT NULL,
                    FOREIGN KEY(creator) REFERENCES users(username))''')

        # ID映射表（修正字段名和约束）
        c.execute('''CREATE TABLE IF NOT EXISTS id_mappings
                    (original_id TEXT NOT NULL,
                    system_id TEXT NOT NULL,
                    group_name TEXT NOT NULL,
                    PRIMARY KEY (original_id, group_name),
                    FOREIGN KEY(system_id) REFERENCES users(username))''')  # 添加外键约束

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()