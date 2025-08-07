import sqlite3
import os
DB_PATH = r'C:\qhwms\qhwms.db'

# 通用数据库连接工具方法
def get_db_conn():
    """获取数据库连接和游标"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    return conn, cursor

def commit_and_close(conn):
    """提交并关闭数据库连接"""
    conn.commit()
    conn.close()

def ensure_db_dir():
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

# ========== draft_order & draft_item ==========
# 建表见 init_db()
def insert_draft_order(customer_id, total_amount, remark, create_time):
    """插入一条暂存出库单主表记录，返回主键draft_id"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        INSERT INTO draft_order (customer_id, total_amount, remark, create_time)
        VALUES (?, ?, ?, ?)
    ''', (customer_id, total_amount, remark, create_time))
    draft_id = cursor.lastrowid
    commit_and_close(conn)
    return draft_id
def insert_draft_item(draft_id, product_id, quantity, price, amount):
    """插入一条暂存出库单明细记录"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        INSERT INTO draft_item (draft_id, product_id, quantity, price, amount)
        VALUES (?, ?, ?, ?, ?)
    ''', (draft_id, product_id, quantity, price, amount))
    commit_and_close(conn)
def get_all_draft_orders():
    """获取所有暂存出库单主表记录（draft_order）"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT draft_id, customer_id, total_amount, remark, create_time FROM draft_order ORDER BY draft_id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
def get_draft_items_by_order(draft_id):
    """获取指定暂存单的所有明细（draft_item）"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT item_id, draft_id, product_id, quantity, price, amount FROM draft_item WHERE draft_id=?", (draft_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
def delete_draft_order(draft_id):
    """根据draft_id删除暂存单主表及所有明细"""
    conn, cursor = get_db_conn()
    cursor.execute("DELETE FROM draft_item WHERE draft_id=?", (draft_id,))
    cursor.execute("DELETE FROM draft_order WHERE draft_id=?", (draft_id,))
    commit_and_close(conn)

# ========== outbound_order & outbound_item ==========
# 建表见 init_db()
def insert_outbound_order(order_no, customer_id, total_amount, pay_status, total_paid, total_debt, create_time):
    """插入一条出库单主表记录，返回主键outbound_id"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        INSERT INTO outbound_order (order_no, customer_id, total_amount, pay_status, total_paid, total_debt, create_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (order_no, customer_id, total_amount, pay_status, total_paid, total_debt, create_time))
    outbound_id = cursor.lastrowid
    commit_and_close(conn)
    return outbound_id
def insert_outbound_item(outbound_id, product_id, quantity, price, amount):
    """插入一条出库单明细记录，含单价price，返回item_id"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        INSERT INTO outbound_item (outbound_id, product_id, quantity, price, amount)
        VALUES (?, ?, ?, ?, ?)
    ''', (outbound_id, product_id, quantity, price, amount))
    item_id = cursor.lastrowid
    commit_and_close(conn)
    return item_id
def get_all_outbound_orders():
    """获取所有出库单主表记录（outbound_order）"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT outbound_id, order_no, customer_id, total_amount, pay_status, total_paid, total_debt, create_time FROM outbound_order ORDER BY outbound_id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
def get_outbound_items_by_order(outbound_id):
    """获取指定出库单的所有明细（outbound_item）"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT item_id, outbound_id, product_id, quantity, price, amount FROM outbound_item WHERE outbound_id=?", (outbound_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
def get_outbound_order_by_id(outbound_id):
    """根据出库单主表id获取记录"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT outbound_id, order_no, customer_id, total_amount, pay_status, total_paid, total_debt, create_time FROM outbound_order WHERE outbound_id=?", (outbound_id,))
    row = cursor.fetchone()
    conn.close()
    return row
def get_outbound_id_by_order_no(order_no):
    conn, cursor = get_db_conn()
    cursor.execute("SELECT outbound_id FROM outbound_order WHERE order_no=?", (order_no,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
def update_outbound_order_amount(outbound_id, total_amount, total_paid, total_debt, pay_status):
    conn, cursor = get_db_conn()
    cursor.execute("UPDATE outbound_order SET total_amount=?, total_paid=?, total_debt=?, pay_status=? WHERE outbound_id=?", (total_amount, total_paid, total_debt, pay_status, outbound_id))
    commit_and_close(conn)
def update_outbound_item_amount(item_id, new_amount):
    conn, cursor = get_db_conn()
    cursor.execute("UPDATE outbound_item SET amount=? WHERE item_id=?", (new_amount, item_id))
    commit_and_close(conn)
def decrease_outbound_item_quantity(item_id, qty):
    conn, cursor = get_db_conn()
    cursor.execute("UPDATE outbound_item SET quantity = quantity - ? WHERE item_id=? AND quantity >= ?", (qty, item_id, qty))
    commit_and_close(conn)

def delete_outbound_item_by_id(item_id):
    conn, cursor = get_db_conn()
    cursor.execute("DELETE FROM outbound_item WHERE item_id=?", (item_id,))
    commit_and_close(conn)
def delete_outbound_order_by_id(outbound_id):
    conn, cursor = get_db_conn()
    cursor.execute("DELETE FROM outbound_order WHERE outbound_id=?", (outbound_id,))
    commit_and_close(conn)

# ========== inventory ==========
# 建表见 init_db()
def insert_inventory_from_stock(stock_id, factory, product_no, size, color,unit, quantity):
    """根据入库信息插入一条库存记录到inventory表"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        INSERT INTO inventory (stock_id, factory, product_no, size, color,unit, quantity)
        VALUES (?, ?, ?, ?, ?,?, ?)
    ''', (stock_id, factory, product_no, size, color,unit, quantity))
    commit_and_close(conn)
def get_all_inventory():
    """获取所有库存表（inventory）记录"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT id, stock_id, factory, product_no, size, color,unit, quantity FROM inventory ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
def get_inventory_by_id(product_id):
    """根据product_id（即inventory.id）获取库存信息，返回(id, factory, product_no, size, color,unit, quantity)"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT id, factory, product_no, size, color,unit, quantity FROM inventory WHERE id=?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return row
def get_inventory_by_id_by_fields(product_no, color, size):
    conn, cursor = get_db_conn()
    cursor.execute("SELECT id, factory, product_no, size, color,unit, quantity FROM inventory WHERE product_no=? AND color=? AND size=?", (product_no, color, size))
    row = cursor.fetchone()
    conn.close()
    return row
def update_inventory_by_stock_id(stock_id, factory, product_no, size, color,unit, in_quantity):
    """根据库存的stock_id同步修改inventory表相关信息"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        UPDATE inventory SET factory=?, product_no=?, size=?, color=?,unit=?, quantity=? WHERE stock_id=?
    ''', (factory, product_no, size, color,unit, in_quantity, stock_id))
    conn.commit()
    conn.close()
def update_inventory_size_by_id(inventory_id, size):
    conn, cursor = get_db_conn()
    cursor.execute("UPDATE inventory SET size=? WHERE id=?", (size, inventory_id))
    commit_and_close(conn)
def increase_inventory_by_id(inventory_id, quantity):
    """根据库存主键id增加库存表(inventory)的数量"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        UPDATE inventory SET quantity = quantity + ? WHERE id=?
    ''', (quantity, inventory_id))
    commit_and_close(conn)
def decrease_inventory(product_no, color, size, quantity):
    """根据货号、颜色、尺码减少库存表(inventory)的数量"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        UPDATE inventory SET quantity = quantity - ? WHERE product_no=? AND color=? AND size=? AND quantity >= ?
    ''', (quantity, product_no, color, size, quantity))
    commit_and_close(conn)
def decrease_inventory_by_id(inventory_id, quantity):
    """根据库存主键id减少库存表(inventory)的数量"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        UPDATE inventory SET quantity = quantity - ? WHERE id=? AND quantity >= ?
    ''', (quantity, inventory_id, quantity))
    commit_and_close(conn)
def delete_inventory_by_stock_id(stock_id):
    """根据入库id删除库存表中对应记录（inventory表）"""
    conn, cursor = get_db_conn()
    cursor.execute("DELETE FROM inventory WHERE stock_id=?", (stock_id,))
    commit_and_close(conn)

# ========== stock ==========
# 建表见 init_db()
def insert_stock(factory, product_no, size, color,unit, in_quantity, price, total, in_date=None):
    """插入一条入库记录到stock表，支持自定义入库时间"""
    import datetime
    conn, cursor = get_db_conn()
    if in_date is None:
        in_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO stock (factory, product_no, size, color,unit, in_quantity, price, total, is_settled, in_date)
        VALUES (?, ?, ?, ?, ?,?, ?, ?, 0, ?)
    ''', (factory, product_no, size, color,unit, in_quantity, price, total, in_date))
    commit_and_close(conn)
def get_all_stock():
    """获取所有入库记录（库存主表）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, factory, product_no, size, color,unit, in_quantity, price, total, is_settled, in_date FROM stock ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
def update_stock_by_id(stock_id, factory, product_no, size, color,unit, in_quantity, price, total):
    """根据id更新入库记录（stock表）"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        UPDATE stock SET factory=?, product_no=?, size=?, color=?,unit=?, in_quantity=?, price=?, total=? WHERE id=?
    ''', (factory, product_no, size, color,unit, in_quantity, price, total, stock_id))
    commit_and_close(conn)
def settle_stock_by_id(stock_id):
    """将指定id的库存记录is_settled字段设为1，可传单个id或id列表"""
    conn, cursor = get_db_conn()
    if isinstance(stock_id, (list, tuple)):
        cursor.executemany("UPDATE stock SET is_settled=1 WHERE id=?", [(i,) for i in stock_id])
    else:
        cursor.execute("UPDATE stock SET is_settled=1 WHERE id=?", (stock_id,))
    commit_and_close(conn)
def delete_stock_by_id(stock_id):
    """根据id删除入库记录（stock表）"""
    conn, cursor = get_db_conn()
    cursor.execute("DELETE FROM stock WHERE id=?", (stock_id,))
    commit_and_close(conn)

# ========== settle_log ==========
# 建表见 init_db()
def insert_settle_log(factory, product_no, size, color, in_quantity, price, total, settle_date):
    """插入一条结账记录到settle_log表"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        INSERT INTO settle_log (factory, product_no, size, color, in_quantity, price, total, settle_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (factory, product_no, size, color, in_quantity, price, total, settle_date))
    commit_and_close(conn)
def get_all_settle_log():
    """获取所有结账记录（settle_log表）"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT factory, product_no, size, color, in_quantity, price, total, settle_date FROM settle_log ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# ========== stock_log ==========
# 建表见 init_db()
def insert_stock_log(factory, product_no, size, color, in_quantity, action_type, action_date):
    """插入一条入库/返厂操作日志到stock_log表"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        INSERT INTO stock_log (factory, product_no, size, color, in_quantity, action_type, action_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (factory, product_no, size, color, in_quantity, action_type, action_date))
    commit_and_close(conn)
def get_all_stock_log():
    """获取所有入库/返厂日志（stock_log表）"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT factory, product_no, size, color, in_quantity, action_type, action_date FROM stock_log ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# ========== customer_info ==========
# 建表见 init_db()
def insert_customer(name, address, phone, logistics_info):
    """插入一条客户信息到customer_info表"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        INSERT INTO customer_info (name, address, phone, logistics_info)
        VALUES (?, ?, ?, ?)
    ''', (name, address, phone, logistics_info))
    commit_and_close(conn)
def get_all_customers():
    """获取所有客户信息（customer_info表）"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT id, name, address, phone, logistics_info FROM customer_info ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
def get_customer_by_id(customer_id):
    """根据客户id获取客户信息"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT id, name, address, phone, logistics_info FROM customer_info WHERE id=?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_outbound_payment_status(outbound_id):
    """同步更新出库单主表的已付/待付金额"""
    conn, cursor = get_db_conn()
    try:
        # 汇总所有payment_record的payment_amount
        cursor.execute("SELECT SUM(payment_amount) FROM payment_record WHERE outbound_id=?", (outbound_id,))
        paid = cursor.fetchone()[0] or 0.0
        
        # 获取主表总金额
        cursor.execute("SELECT total_amount FROM outbound_order WHERE outbound_id=?", (outbound_id,))
        total = cursor.fetchone()[0] or 0.0
        debt = total - paid
        
        # 更新主表
        pay_status = 2 if debt <= 0.01 else (1 if paid > 0 else 0)
        cursor.execute("UPDATE outbound_order SET total_paid=?, total_debt=?, pay_status=? WHERE outbound_id=?", 
                      (paid, debt, pay_status, outbound_id))
        
        conn.commit()
    finally:
        conn.close()
def update_customer(cid, name, address, phone, logistics_info):
    """根据id更新客户信息（customer_info表）"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        UPDATE customer_info SET name=?, address=?, phone=?, logistics_info=? WHERE id=?
    ''', (name, address, phone, logistics_info, cid))
    commit_and_close(conn)
def delete_customer(cid):
    """根据id删除客户信息（customer_info表）"""
    conn, cursor = get_db_conn()
    cursor.execute("DELETE FROM customer_info WHERE id=?", (cid,))
    commit_and_close(conn)

# ========== users ==========
# 建表见 init_db()
def insert_user(username, account, password, role=1):
    """新增用户，默认库管权限（role=1），管理员为0"""
    conn, cursor = get_db_conn()
    cursor.execute("INSERT INTO users (username, account, password, role) VALUES (?, ?, ?, ?)", (username, account, password, role))
    commit_and_close(conn)
def get_all_users():
    """获取所有用户信息"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT id, username, account, role FROM users ORDER BY id DESC")
    users = cursor.fetchall()
    conn.close()
    return users
def get_user_by_id(user_id):
    """根据id获取用户信息"""
    conn, cursor = get_db_conn()
    cursor.execute("SELECT id, username, account, role FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user
def update_user(user_id, username=None, account=None, password=None, role=None):
    """修改用户信息，参数为None则不更新该字段"""
    conn, cursor = get_db_conn()
    fields = []
    values = []
    if username is not None:
        fields.append("username=?")
        values.append(username)
    if account is not None:
        fields.append("account=?")
        values.append(account)
    if password is not None:
        fields.append("password=?")
        values.append(password)
    if role is not None:
        fields.append("role=?")
        values.append(role)
    if not fields:
        conn.close()
        return False
    sql = f"UPDATE users SET {', '.join(fields)} WHERE id=?"
    values.append(user_id)
    cursor.execute(sql, tuple(values))
    commit_and_close(conn)
    return True
def delete_user(user_id):
    """根据id删除用户"""
    conn, cursor = get_db_conn()
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    commit_and_close(conn)

# ========== payment_record ==========
# 建表见 init_db()
def insert_payment_record(outbound_id, item_ids, payment_amount, pay_time,pay_method):
    """插入一条支付记录"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        INSERT INTO payment_record (outbound_id, item_ids, payment_amount, pay_time,pay_method)
        VALUES (?, ?, ?, ?,?)
    ''', (outbound_id, item_ids, payment_amount, pay_time,pay_method))
    commit_and_close(conn)
def get_all_payment_records():
    conn, cursor = get_db_conn()
    try:
        cursor.execute("SELECT payment_id, outbound_id, item_ids, payment_amount, pay_time, pay_method FROM payment_record ORDER BY payment_id DESC")
    except Exception:
        cursor.execute("SELECT payment_id, outbound_id, item_ids, payment_amount, pay_time FROM payment_record ORDER BY payment_id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# ========== debt_record ==========
# 建表见 init_db()
def insert_debt_record(outbound_id, item_ids, remaining_debt):
    """插入一条欠账记录"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        INSERT INTO debt_record (outbound_id, item_ids, remaining_debt)
        VALUES (?, ?, ?)
    ''', (outbound_id, item_ids, remaining_debt))
    commit_and_close(conn)
def get_all_debt_records():
    conn, cursor = get_db_conn()
    cursor.execute("SELECT debt_id, outbound_id, item_ids, remaining_debt FROM debt_record ORDER BY debt_id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
def delete_debt_record_by_outboundid(outbound_id):
    """根据id删除欠账记录"""
    conn, cursor = get_db_conn()
    cursor.execute("DELETE FROM debt_record WHERE outbound_id=?", (outbound_id,))
    commit_and_close(conn)

def get_order_details(outbound_ids, start_date=None, end_date=None):
    """
    根据订单ID获取订单详情，并支持日期范围筛选
    :param outbound_ids: 订单ID列表
    :param start_date: 开始日期 (YYYY-MM-DD)
    :param end_date: 结束日期 (YYYY-MM-DD)
    :return: 订单详情列表
    """
    order_details = []
    conn, cursor = get_db_conn()
    try:
        for order_id in outbound_ids:
            # 查询订单信息
            cursor.execute("SELECT order_no, create_time FROM outbound_order WHERE outbound_id = ?", (order_id.strip(),))
            order_info = cursor.fetchone()
            if not order_info:
                continue

            order_no, outbound_date = order_info

            # 截取出库日期的日期部分
            if ' ' in outbound_date:
                outbound_date = outbound_date.split(' ')[0]

            # 日期范围筛选
            if start_date or end_date:
                order_date = outbound_date.split(' ')[0] if ' ' in outbound_date else outbound_date
                if start_date and order_date < start_date:
                    continue
                if end_date and order_date > end_date:
                    continue

            # 查询订单项
            cursor.execute("SELECT product_id, quantity, price, amount FROM outbound_item WHERE outbound_id = ?", (order_id.strip(),))
            items = cursor.fetchall()

            for item in items:
                product_id, quantity, price, amount = item
                
                # 查询库存信息获取产品详情
                cursor.execute("SELECT product_no, color, unit, size FROM inventory WHERE id = ?", (product_id,))
                inventory_info = cursor.fetchone()
                if not inventory_info:
                    product_no, product_color, unit, size = "", "", "", ""
                else:
                    product_no, product_color, unit, size = inventory_info

                order_details.append([
                    order_no,
                    outbound_date,
                    product_no,
                    product_color,
                    unit,
                    size,
                    quantity,
                    f"{price:.2f}",
                    f"{amount:.2f}"
                ])
    finally:
        conn.close()
    return order_details

def init_db():
    """初始化数据库，创建所有表结构，插入默认管理员账户"""
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 对账单表（Statement）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            statement_no TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            outbound_ids TEXT NOT NULL, -- 多个订单ID用逗号分隔
            previous_debt REAL NOT NULL DEFAULT 0,
            current_debt REAL NOT NULL DEFAULT 0,
            total_amount REAL NOT NULL DEFAULT 0,
            bill_period TEXT NOT NULL,
            issue_date TEXT NOT NULL
        )
    ''')
    
    # 新增暂存出库单主表（draft_order）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS draft_order (
            draft_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            total_amount REAL NOT NULL,
            remark TEXT,
            create_time TEXT
        )
    ''')
    # 新增暂存出库单明细表（draft_item）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS draft_item (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_id INTEGER NOT NULL,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            amount REAL NOT NULL,
            FOREIGN KEY(draft_id) REFERENCES draft_order(draft_id)
        )
    ''')
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
            password TEXT NOT NULL,
            role INTEGER NOT NULL DEFAULT 1 -- 0:管理员, 1:库管
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
            is_settled INTEGER NOT NULL DEFAULT 0,
            in_date TEXT,
            unit TEXT
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
            unit TEXT,
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
    # 新出库单明细表（OutboundItem）增加price字段
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outbound_item (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            outbound_id INTEGER NOT NULL,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            amount REAL NOT NULL,
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
    cursor.execute('SELECT * FROM users WHERE account=?', ("admin",))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (username, account, password, role) VALUES (?, ?, ?, ?)
        ''', ("管理员", "admin", "admin", 0))
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

def insert_debt_record(outbound_id, item_ids, remaining_debt):
    """插入一条欠账记录到debt_record表"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        INSERT INTO debt_record (outbound_id, item_ids, remaining_debt)
        VALUES (?, ?, ?)
    ''', (outbound_id, item_ids, remaining_debt))
    debt_id = cursor.lastrowid
    commit_and_close(conn)
    return debt_id

def insert_payment_record(outbound_id, item_ids, payment_amount, pay_time, pay_method=''):
    """插入一条付款记录到payment_record表"""
    conn, cursor = get_db_conn()
    cursor.execute('''
        INSERT INTO payment_record (outbound_id, item_ids, payment_amount, pay_time, pay_method)
        VALUES (?, ?, ?, ?, ?)
    ''', (outbound_id, item_ids, payment_amount, pay_time, pay_method))
    payment_id = cursor.lastrowid
    commit_and_close(conn)
    return payment_id


def get_debt_record_by_outbound_id(outbound_id):
    """根据出库单ID获取余款记录"""
    conn, cursor = get_db_conn()
    cursor.execute('SELECT * FROM debt_record WHERE outbound_id=?', (outbound_id,))
    result = cursor.fetchone()
    commit_and_close(conn)
    return result


def update_debt_record(debt_id, remaining_debt):
    """更新余款记录"""
    conn, cursor = get_db_conn()
    cursor.execute('UPDATE debt_record SET remaining_debt=? WHERE debt_id=?', (remaining_debt, debt_id))
    commit_and_close(conn)
    return cursor.rowcount > 0


def delete_debt_record_by_id(debt_id):
    """根据ID删除余款记录"""
    conn, cursor = get_db_conn()
    cursor.execute('DELETE FROM debt_record WHERE debt_id=?', (debt_id,))
    commit_and_close(conn)
    return cursor.rowcount > 0


def delete_debt_record_by_outboundid(outbound_id):
    """根据出库单ID删除余款记录"""
    conn, cursor = get_db_conn()
    cursor.execute('DELETE FROM debt_record WHERE outbound_id=?', (outbound_id,))
    commit_and_close(conn)
    return cursor.rowcount > 0


if __name__ == "__main__":
    init_db()