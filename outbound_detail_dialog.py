import tkinter as tk
from tkinter import ttk
from util import dbutil

def show_outbound_detail(parent, order_no):
    # 获取出库单主表信息
    all_orders = dbutil.get_all_outbound_orders()
    order = next((o for o in all_orders if o[1] == order_no), None)
    if not order:
        tk.messagebox.showerror("错误", "未找到该出库单！")
        return
    outbound_id = order[0]
    items = dbutil.get_outbound_items_by_order(outbound_id)
    # 弹窗
    win = tk.Toplevel(parent)
    win.title(f"出库单详情 - {order_no}")
    win.geometry("950x600")
    # 顶部标题
    ttk.Label(win, text="千辉鞋业出库单", font=("微软雅黑", 16, "bold"), foreground="#2a5d2a").pack(pady=(16, 6))
    # 获取客户信息
    customer = dbutil.get_all_customers()
    customer_map = {c[0]: c for c in customer}
    cust = customer_map.get(order[2], None)
    cust_name = cust[1] if cust else f"ID:{order[2]}"
    cust_addr = cust[2] if cust else ""
    logistics = cust[4] if cust else ""
    # 第二行：订单号、客户姓名、地址、出库日期
    row2 = ttk.Frame(win)
    row2.pack(fill=tk.X, padx=24, pady=2)
    ttk.Label(row2, text=f"订单号: {order_no}", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(0, 18))
    ttk.Label(row2, text=f"客户: {cust_name}", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(0, 18))
    ttk.Label(row2, text=f"地址: {cust_addr}", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(0, 18))
    ttk.Label(row2, text=f"出库日期: {order[7]}", font=("微软雅黑", 11)).pack(side=tk.LEFT)
    # 第三行：物流信息
    ttk.Label(win, text=f"物流信息: {logistics}", font=("微软雅黑", 11)).pack(anchor=tk.W, padx=24, pady=(0, 8))
    # 明细表格
    columns = ("idx", "product_no", "color", "quantity", "price", "amount", "item_pay_status", "debt_amount")
    headers = [
        ("idx", "序号"),
        ("product_no", "货号"),
        ("color", "颜色"),
        ("quantity", "出库数量"),
        ("price", "单价"),
        ("amount", "合计"),
        ("item_pay_status", "支付状态"),
        ("debt_amount", "余款金额")
    ]
    tree = ttk.Treeview(win, columns=columns, show="headings", height=15)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=90)
    tree.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)
    total_amount = 0.0
    total_paid = 0.0
    total_debt = 0.0
    for idx, item in enumerate(items, 1):
        inv = dbutil.get_inventory_by_id(item[2])
        product_no = inv[2] if inv else ''
        color = inv[4] if inv else ''
        quantity = item[3]
        amount = item[4]
        # 单价=合计/数量，避免除0
        price = amount / quantity if quantity else 0.0
        total_amount += amount
        paid = item[6] if len(item) > 6 else 0
        total_paid += paid
        debt = item[7] if len(item) > 7 else 0
        total_debt += debt
        tree.insert('', tk.END, values=(
            idx, product_no, color, quantity, f"{price:.2f}", f"{amount:.2f}",
            "已付" if item[5]==1 else "欠款", f"{debt:.2f}"
        ))
    # 右下角统计和按钮
    bottom = ttk.Frame(win)
    bottom.pack(fill=tk.X, side=tk.BOTTOM, anchor=tk.SE, padx=24, pady=12)
    # 复选框切换库房/门市
    is_kufang = tk.BooleanVar(value=True)
    def update_view():
        show_kufang = is_kufang.get()
        # 列名、宽度、显示/隐藏
        show_cols = ["idx", "product_no", "color", "quantity"]
        if not show_kufang:
            show_cols += ["price", "amount", "item_pay_status", "debt_amount"]
        tree['displaycolumns'] = show_cols
        # 统计区显示
        for w in bottom.pack_slaves():
            w.pack_forget()
        btn_print.pack(side=tk.RIGHT, padx=(0, 12))
        chk.pack(side=tk.RIGHT, padx=(0, 12))

        ttk.Label(bottom, text=f"总计数量: {int(total_qty)}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
        if not show_kufang:
            ttk.Label(bottom, text=f"余款总计: {total_debt:.2f}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
            ttk.Label(bottom, text=f"已缴总计: {total_paid:.2f}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
            ttk.Label(bottom, text=f"总计金额: {total_amount:.2f}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
    btn_print = ttk.Button(bottom, text="打印出库单", width=14)
    chk = ttk.Checkbutton(bottom, text="库房出库单", variable=is_kufang, command=update_view)
    # 统计数量
    total_qty = sum(item[3] for item in items)
    update_view()
