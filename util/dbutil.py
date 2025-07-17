import os
import sqlite3
# 根据item_id减少outbound_item表中的quantity
def decrease_outbound_item_quantity(item_id, qty):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE outbound_item SET quantity = quantity - ? WHERE item_id=? AND quantity >= ?", (qty, item_id, qty))
    conn.commit()
    conn.close()

# 根据order_no查找outbound_id
def get_outbound_id_by_order_no(order_no):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT outbound_id FROM outbound_order WHERE order_no=?", (order_no,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# 根据item_id减少returnable_qty
def decrease_returnable_qty_by_item_id(item_id, qty):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE outbound_item SET returnable_qty = returnable_qty - ? WHERE item_id=? AND returnable_qty >= ?", (qty, item_id, qty))
    conn.commit()
    conn.close()

# 根据货号、颜色、尺码查找库存
def get_inventory_by_id_by_fields(product_no, color, size):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, factory, product_no, size, color, quantity FROM inventory WHERE product_no=? AND color=? AND size=?", (product_no, color, size))
    row = cursor.fetchone()
    conn.close()
    return row

# 增加库存数量
def increase_inventory_by_id(inventory_id, quantity):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE id=?", (quantity, inventory_id))
    conn.commit()
    conn.close()

# 根据outbound_id获取出库单主表信息
def get_outbound_order_by_id(outbound_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM outbound_order WHERE outbound_id=?", (outbound_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# 根据customer_id获取客户信息
def get_customer_by_id(customer_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customer_info WHERE id=?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# 新增：根据id更新inventory表的size字段
def update_inventory_size_by_id(inventory_id, size):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET size=? WHERE id=?", (size, inventory_id))
    conn.commit()
    conn.close()
# 通过product_id获取库存信息（货号/颜色/尺码等）
def get_inventory_by_id(product_id):
    """根据product_id（即inventory.id）获取库存信息，返回(id, factory, product_no, size, color, quantity)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, factory, product_no, size, color, quantity FROM inventory WHERE id=?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return row


# 新出库单主表插入
def insert_outbound_order(order_no, customer_id, total_amount, pay_status, total_paid, total_debt, create_time):
    """插入一条出库单主表记录，返回主键outbound_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO outbound_order (order_no, customer_id, total_amount, pay_status, total_paid, total_debt, create_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (order_no, customer_id, total_amount, pay_status, total_paid, total_debt, create_time))
    outbound_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return outbound_id

# 新出库单明细插入
def insert_outbound_item(outbound_id, product_id, quantity, amount, item_pay_status, paid_amount, debt_amount, returnable_qty):
    """插入一条出库单明细记录（去除product_no、color、size）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO outbound_item (outbound_id, product_id, quantity, amount, item_pay_status, paid_amount, debt_amount, returnable_qty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (outbound_id, product_id, quantity, amount, item_pay_status, paid_amount, debt_amount, returnable_qty))
    conn.commit()
    conn.close()

# 新增支付记录
def insert_payment_record(outbound_id, item_ids, payment_amount, pay_time,pay_method):
    """插入一条支付记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payment_record (outbound_id, item_ids, payment_amount, pay_time,pay_method)
        VALUES (?, ?, ?, ?,?)
    ''', (outbound_id, item_ids, payment_amount, pay_time,pay_method))
    conn.commit()
    conn.close()

# 新增欠账记录
def insert_debt_record(outbound_id, item_ids, remaining_debt):
    """插入一条欠账记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO debt_record (outbound_id, item_ids, remaining_debt)
        VALUES (?, ?, ?)
    ''', (outbound_id, item_ids, remaining_debt))
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


# 获取所有出库单主表
def get_all_outbound_orders():
    """获取所有出库单主表记录（outbound_order）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT outbound_id, order_no, customer_id, total_amount, pay_status, total_paid, total_debt, create_time FROM outbound_order ORDER BY outbound_id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# 获取指定出库单的所有明细
def get_outbound_items_by_order(outbound_id):
    """获取指定出库单的所有明细（outbound_item）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, outbound_id, product_id, quantity, amount, item_pay_status, paid_amount, debt_amount, returnable_qty FROM outbound_item WHERE outbound_id=?", (outbound_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# 获取所有支付记录
def get_all_payment_records():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT payment_id, outbound_id, item_ids, payment_amount, pay_time, pay_method FROM payment_record ORDER BY payment_id DESC")
    except Exception:
        cursor.execute("SELECT payment_id, outbound_id, item_ids, payment_amount, pay_time FROM payment_record ORDER BY payment_id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# 获取所有欠账记录
def get_all_debt_records():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT debt_id, outbound_id, item_ids, remaining_debt FROM debt_record ORDER BY debt_id DESC")
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
    # 新出库单主表（OutboundOrder）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outbound_order (
            outbound_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT NOT NULL,
            customer_id INTEGER,
            total_amount REAL NOT NULL,
            pay_status INTEGER NOT NULL DEFAULT 0, -- 0未支付/1部分/2全额
            total_paid REAL NOT NULL DEFAULT 0,
            total_debt REAL NOT NULL DEFAULT 0,
            create_time TEXT
        )
    ''')
    # 新出库单明细表（OutboundItem）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outbound_item (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            outbound_id INTEGER NOT NULL,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            amount REAL NOT NULL,
            item_pay_status INTEGER NOT NULL DEFAULT 0, -- 0未付/1已付
            paid_amount REAL NOT NULL DEFAULT 0,
            debt_amount REAL NOT NULL DEFAULT 0,
            returnable_qty INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(outbound_id) REFERENCES outbound_order(outbound_id)
        )
    ''')
    # 新支付记录表（PaymentRecord）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_record (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            outbound_id INTEGER NOT NULL,
            item_ids TEXT,
            payment_amount REAL NOT NULL,
            pay_time TEXT,
            pay_method TEXT,
            FOREIGN KEY(outbound_id) REFERENCES outbound_order(outbound_id)
        )
    ''')
    # 新欠账记录表（DebtRecord）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debt_record (
            debt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            outbound_id INTEGER NOT NULL,
            item_ids TEXT,
            remaining_debt REAL NOT NULL,
            FOREIGN KEY(outbound_id) REFERENCES outbound_order(outbound_id)
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