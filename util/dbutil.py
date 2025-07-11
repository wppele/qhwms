import sqlite3
import os
# 插入出库单记录
def insert_outbound_order(order_no, customer_name, address, logistics_info, product_no, color, size, quantity, price, total, outbound_date, is_paid, pay_method, pay_date):
    """插入一条出库单记录到outbound_order表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO outbound_order (order_no, customer_name, address, logistics_info, product_no, color, size, quantity, price, total, outbound_date, is_paid, pay_method, pay_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (order_no, customer_name, address, logistics_info, product_no, color, size, quantity, price, total, outbound_date, is_paid, pay_method, pay_date))
    conn.commit()
    conn.close()

def decrease_inventory(product_no, color, size, quantity):
    """根据货号、颜色、尺码减少库存表(inventory)的数量"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE inventory SET quantity = quantity - ? WHERE product_no=? AND color=? AND size=? AND quantity >= ?
    ''', (quantity, product_no, color, size, quantity))
    conn.commit()
    conn.close()

# 根据库存主键id减少库存数量
def decrease_inventory_by_id(inventory_id, quantity):
    """根据库存主键id减少库存表(inventory)的数量"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE inventory SET quantity = quantity - ? WHERE id=? AND quantity >= ?
    ''', (quantity, inventory_id, quantity))
    conn.commit()
    conn.close()

# 获取所有出库单记录（outbound_order表）
def get_all_outbound_orders():
    """获取所有出库单记录（outbound_order表）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, order_no, customer_name, address, logistics_info, product_no, color, size, quantity, price, total, outbound_date, is_paid, pay_method, pay_date FROM outbound_order ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qhwms.db')

def init_db():
    """初始化数据库，创建所有表结构，插入默认管理员账户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 创建用户表
    # 字段说明：
    #   id: 主键，自增
    #   username: 用户名
    #   account: 登录账号，唯一
    #   password: 登录密码
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            account TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # 创建库存表（stock，去掉available_quantity）
    # 字段说明：
    #   id: 主键，自增
    #   factory: 厂家
    #   product_no: 货号
    #   color: 颜色
    #   size: 尺码
    #   in_quantity: 入库数量
    #   price: 单价
    #   total: 合计
    #   is_settled: 是否结账（0未结账，1已结账）
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
    # 结账记录表（settle_log）
    # 字段说明：
    #   id: 主键，自增
    #   factory: 厂家
    #   product_no: 货号
    #   size: 尺码
    #   color: 颜色
    #   in_quantity: 数量
    #   price: 单价
    #   total: 合计
    #   settle_date: 结账日期
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
    # 入库/返厂记录表（stock_log）
    # 字段说明：
    #   id: 主键，自增
    #   factory: 厂家
    #   product_no: 货号
    #   size: 尺码
    #   color: 颜色
    #   in_quantity: 数量
    #   action_type: 操作类型（入库/返厂）
    #   action_date: 操作日期
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
    # 字段说明：
    #   id: 主键，自增
    #   stock_id: 入库表id（外键）
    #   factory: 厂家
    #   product_no: 货号
    #   size: 尺码
    #   color: 颜色
    #   quantity: 库存数量
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
    # 新增客户信息表（customer_info）
    # 字段说明：
    #   id: 主键，自增
    #   name: 客户名称
    #   address: 地址
    #   phone: 电话
    #   logistics_info: 物流信息（分号拼接字符串）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            logistics_info TEXT
        )
    ''')
    # 新增出库单表（outbound_order）
    # 字段说明：
    #   id: 主键，自增
    #   order_no: 订单号（字符串）
    #   customer_name: 客户姓名
    #   address: 客户地址
    #   logistics_info: 物流信息
    #   product_no: 货号
    #   color: 颜色
    #   size: 尺码
    #   quantity: 出库数量
    #   price: 单价
    #   total: 合计
    #   outbound_date: 出库日期
    #   is_paid: 是否付款（0未付款，1已付款）
    #   pay_method: 付款方式
    #   pay_date: 付款日期
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outbound_order (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            address TEXT,
            logistics_info TEXT,
            product_no TEXT NOT NULL,
            color TEXT,
            size TEXT,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            outbound_date TEXT NOT NULL,
            is_paid INTEGER NOT NULL DEFAULT 0,
            pay_method TEXT,
            pay_date TEXT
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
    """校验用户账号和密码，返回是否存在该用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE account=? AND password=?', (account, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def get_username_by_account(account):
    """根据账号获取用户名，若无则返回账号本身"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE account=?", (account,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else account

def get_all_stock():
    """获取所有入库记录（库存主表）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, factory, product_no, size, color, in_quantity, price, total, is_settled FROM stock ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def insert_stock(factory, product_no, size, color, in_quantity, price, total):
    """插入一条入库记录到stock表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO stock (factory, product_no, size, color, in_quantity, price, total, is_settled)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    ''', (factory, product_no, size, color, in_quantity, price, total))
    conn.commit()
    conn.close()

def delete_stock_by_id(stock_id):
    """根据id删除入库记录（stock表）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stock WHERE id=?", (stock_id,))
    conn.commit()
    conn.close()

def update_stock_by_id(stock_id, factory, product_no, size, color, in_quantity, price, total):
    """根据id更新入库记录（stock表）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE stock SET factory=?, product_no=?, size=?, color=?, in_quantity=?, price=?, total=? WHERE id=?
    ''', (factory, product_no, size, color, in_quantity, price, total, stock_id))
    conn.commit()
    conn.close()

def settle_stock_by_id(stock_id):
    """将指定id的库存记录is_settled字段设为1，可传单个id或id列表"""
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
    """插入一条结账记录到settle_log表"""
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
    """插入一条入库/返厂操作日志到stock_log表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO stock_log (factory, product_no, size, color, in_quantity, action_type, action_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (factory, product_no, size, color, in_quantity, action_type, action_date))
    conn.commit()
    conn.close()

def insert_inventory_from_stock(stock_id, factory, product_no, size, color, quantity):
    """根据入库信息插入一条库存记录到inventory表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO inventory (stock_id, factory, product_no, size, color, quantity)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (stock_id, factory, product_no, size, color, quantity))
    conn.commit()
    conn.close()

def get_all_inventory():
    """获取所有库存表（inventory）记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, stock_id, factory, product_no, size, color, quantity FROM inventory ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_settle_log():
    """获取所有结账记录（settle_log表）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT factory, product_no, size, color, in_quantity, price, total, settle_date FROM settle_log ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_stock_log():
    """获取所有入库/返厂日志（stock_log表）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT factory, product_no, size, color, in_quantity, action_type, action_date FROM stock_log ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# 根据stock_id删除库存表中对应记录
def delete_inventory_by_stock_id(stock_id):
    """根据入库id删除库存表中对应记录（inventory表）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE stock_id=?", (stock_id,))
    conn.commit()
    conn.close()

def get_all_customers():
    """获取所有客户信息（customer_info表）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, address, phone, logistics_info FROM customer_info ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def insert_customer(name, address, phone, logistics_info):
    """插入一条客户信息到customer_info表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO customer_info (name, address, phone, logistics_info)
        VALUES (?, ?, ?, ?)
    ''', (name, address, phone, logistics_info))
    conn.commit()
    conn.close()

def update_customer(cid, name, address, phone, logistics_info):
    """根据id更新客户信息（customer_info表）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE customer_info SET name=?, address=?, phone=?, logistics_info=? WHERE id=?
    ''', (name, address, phone, logistics_info, cid))
    conn.commit()
    conn.close()

def delete_customer(cid):
    """根据id删除客户信息（customer_info表）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customer_info WHERE id=?", (cid,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()