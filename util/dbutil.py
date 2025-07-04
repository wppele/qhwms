import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qhwms.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 创建用户表，字段为username、account、password
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            account TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # 创建库存表（数量改为in_quantity，新增available_quantity）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factory TEXT NOT NULL,
            product_no TEXT NOT NULL,
            color TEXT,
            size TEXT,
            in_quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            available_quantity INTEGER NOT NULL,
            is_settled INTEGER NOT NULL DEFAULT 0
        )
    ''')
    # 检查admin账户是否存在，不存在则插入
    cursor.execute('SELECT * FROM users WHERE account=?', ("a",))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (username, account, password) VALUES (?, ?, ?)
        ''', ("管理员", "a", "a"))
    conn.commit()
    conn.close()

def check_user(account, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE account=? AND password=?', (account, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def get_username_by_account(account):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE account=?", (account,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else account

def get_all_stock():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, factory, product_no, size, color, in_quantity, price, total, available_quantity, is_settled FROM stock ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def insert_stock(factory, product_no, size, color, in_quantity, price, total):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO stock (factory, product_no, size, color, in_quantity, price, total, available_quantity, is_settled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    ''', (factory, product_no, size, color, in_quantity, price, total, in_quantity))
    conn.commit()
    conn.close()

def delete_stock_by_id(stock_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stock WHERE id=?", (stock_id,))
    conn.commit()
    conn.close()

def update_stock_by_id(stock_id, factory, product_no, size, color, in_quantity, available_quantity, price, total):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE stock SET factory=?, product_no=?, size=?, color=?, in_quantity=?, price=?, total=?, available_quantity=? WHERE id=?
    ''', (factory, product_no, size, color, in_quantity, available_quantity, price, total, stock_id))
    conn.commit()
    conn.close()

def settle_stock_by_id(stock_id):
    """
    将指定id的库存记录is_settled字段设为1，可传单个id或id列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if isinstance(stock_id, (list, tuple)):
        cursor.executemany("UPDATE stock SET is_settled=1 WHERE id=?", [(i,) for i in stock_id])
    else:
        cursor.execute("UPDATE stock SET is_settled=1 WHERE id=?", (stock_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()