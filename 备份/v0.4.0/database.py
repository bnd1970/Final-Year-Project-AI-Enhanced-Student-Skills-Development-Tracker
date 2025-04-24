import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "collab_system.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password_hash TEXT,
                  role TEXT CHECK(role IN ('leader', 'member')),
                  group_id INTEGER,
                  FOREIGN KEY(group_id) REFERENCES groups(id))''')
                 
    # 群组表
    c.execute('''CREATE TABLE IF NOT EXISTS groups
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE,
                  creator_id INTEGER,
                  FOREIGN KEY(creator_id) REFERENCES users(id))''')
    
    # 评估结果表
    c.execute('''CREATE TABLE IF NOT EXISTS evaluations
                 (id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  evaluation_date DATE,
                  participation INTEGER CHECK(participation BETWEEN 0 AND 5),
                  initiative INTEGER CHECK(initiative BETWEEN 0 AND 5),
                  problem_solving INTEGER CHECK(problem_solving BETWEEN 0 AND 5),
                  coordination INTEGER CHECK(coordination BETWEEN 0 AND 5),
                  responsiveness INTEGER CHECK(responsiveness BETWEEN 0 AND 5),
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
                 
    conn.commit()
    conn.close()

if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    init_db()