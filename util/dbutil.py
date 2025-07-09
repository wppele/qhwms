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
    # 创建库存表（去掉available_quantity）
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
            is_settled INTEGER NOT NULL DEFAULT 0
        )
    ''')
    # 结账记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settle_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factory TEXT,
            product_no TEXT,
            size TEXT,
            color TEXT,
            in_quantity INTEGER,
            price REAL,
            total REAL,
            settle_date TEXT
        )
    ''')
    # 入库/返厂记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factory TEXT,
            product_no TEXT,
            size TEXT,
            color TEXT,
            in_quantity INTEGER,
            action_type TEXT, -- 入库/返厂
            action_date TEXT
        )
    ''')
    # 新增库存表（inventory），入库id为外键，库存数量等于入库数量
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id INTEGER NOT NULL,
            factory TEXT NOT NULL,
            product_no TEXT NOT NULL,
            size TEXT,
            color TEXT,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(stock_id) REFERENCES stock(id)
        )
    ''')
    # 新增客户信息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            logistics_info TEXT
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
    cursor.execute("SELECT id, factory, product_no, size, color, in_quantity, price, total, is_settled FROM stock ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def insert_stock(factory, product_no, size, color, in_quantity, price, total):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO stock (factory, product_no, size, color, in_quantity, price, total, is_settled)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    ''', (factory, product_no, size, color, in_quantity, price, total))
    conn.commit()
    conn.close()

def delete_stock_by_id(stock_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stock WHERE id=?", (stock_id,))
    conn.commit()
    conn.close()

def update_stock_by_id(stock_id, factory, product_no, size, color, in_quantity, price, total):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE stock SET factory=?, product_no=?, size=?, color=?, in_quantity=?, price=?, total=? WHERE id=?
    ''', (factory, product_no, size, color, in_quantity, price, total, stock_id))
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

# 插入结账记录
def insert_settle_log(factory, product_no, size, color, in_quantity, price, total, settle_date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO settle_log (factory, product_no, size, color, in_quantity, price, total, settle_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (factory, product_no, size, color, in_quantity, price, total, settle_date))
    conn.commit()
    conn.close()

# 插入入库/返厂记录
def insert_stock_log(factory, product_no, size, color, in_quantity, action_type, action_date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO stock_log (factory, product_no, size, color, in_quantity, action_type, action_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (factory, product_no, size, color, in_quantity, action_type, action_date))
    conn.commit()
    conn.close()

def insert_inventory_from_stock(stock_id, factory, product_no, size, color, quantity):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO inventory (stock_id, factory, product_no, size, color, quantity)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (stock_id, factory, product_no, size, color, quantity))
    conn.commit()
    conn.close()

def get_all_inventory():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, stock_id, factory, product_no, size, color, quantity FROM inventory ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_settle_log():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT factory, product_no, size, color, in_quantity, price, total, settle_date FROM settle_log ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_stock_log():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT factory, product_no, size, color, in_quantity, action_type, action_date FROM stock_log ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# 根据stock_id删除库存表中对应记录
def delete_inventory_by_stock_id(stock_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE stock_id=?", (stock_id,))
    conn.commit()
    conn.close()

def get_all_customers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, address, phone, logistics_info FROM customer_info ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def insert_customer(name, address, phone, logistics_info):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO customer_info (name, address, phone, logistics_info)
        VALUES (?, ?, ?, ?)
    ''', (name, address, phone, logistics_info))
    conn.commit()
    conn.close()

def update_customer(cid, name, address, phone, logistics_info):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE customer_info SET name=?, address=?, phone=?, logistics_info=? WHERE id=?
    ''', (name, address, phone, logistics_info, cid))
    conn.commit()
    conn.close()

def delete_customer(cid):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customer_info WHERE id=?", (cid,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()