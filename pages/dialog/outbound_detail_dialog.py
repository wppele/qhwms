import tkinter as tk
from tkinter import ttk
from util import dbutil
from util.pdfutil import PDFUtil

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
    ttk.Label(row2, text=f"出库日期: {order[7][:10]}", font=("微软雅黑", 11)).pack(side=tk.LEFT)
    # 第三行：物流信息
    ttk.Label(win, text=f"物流信息: {logistics}", font=("微软雅黑", 11)).pack(anchor=tk.W, padx=24, pady=(0, 8))
    # 明细表格
    columns = ("idx", "product_no", "color", "unit", "size", "quantity", "price", "amount")
    headers = [
        ("idx", "序号"),
        ("product_no", "货号"),
        ("color", "颜色"),
        ("unit", "单位"),
        ("size", "尺码"),
        ("quantity", "出库数量"),
        ("price", "单价"),
        ("amount", "合计"),

    ]
    tree = ttk.Treeview(win, columns=columns, show="headings", height=15)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=90)
    tree.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)
    total_amount = 0.0
    # 从出库单主表获取已付金额和未支付金额
    total_paid = order[5] if len(order) > 5 else 0.0
    total_debt = order[6] if len(order) > 6 else 0.0
    for idx, item in enumerate(items, 1):
        inv = dbutil.get_inventory_by_id(item[2])
        product_no = inv[2] if inv else ''
        color = inv[4] if inv else ''
        unit = inv[5] if inv else ''
        size = inv[3] if inv else ''
        quantity = item[3]
        price = item[4] if len(item) > 4 else 0.0
        amount = item[5] if len(item) > 5 else 0.0
        total_amount += amount
        tree.insert('', tk.END, values=(
            idx, product_no, color, unit, size, quantity, f"{price:.2f}", f"{amount:.2f}"
        ))
    # 右下角统计和按钮
    bottom = ttk.Frame(win)
    bottom.pack(fill=tk.X, side=tk.BOTTOM, anchor=tk.SE, padx=24, pady=12)
    is_kufang = tk.BooleanVar(value=True)
    
    # 备注信息显示
    remark_frame = ttk.Frame(bottom)
    remark_frame.pack(fill=tk.X, padx=0, pady=(0, 10))
    ttk.Label(remark_frame, text="备注信息:", font=('微软雅黑', 11)).pack(side=tk.LEFT)
    remark = order[8] if len(order) > 8 else "无"
    ttk.Label(remark_frame, text=remark, font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=5)

    # 总计信息显示框架
    total_frame = ttk.Frame(bottom)
    total_frame.pack(side=tk.LEFT, padx=(0, 20))
    
    ttk.Label(total_frame, text="总计数量:", font=('微软雅黑', 11)).pack(side=tk.LEFT)
    total_quantity_var = tk.StringVar(value=f"{int(sum(item[3] for item in items))}")
    ttk.Label(total_frame, textvariable=total_quantity_var, font=('微软雅黑', 11, 'bold')).pack(side=tk.LEFT, padx=(5, 15))
    
    ttk.Label(total_frame, text="总计金额:", font=('微软雅黑', 11)).pack(side=tk.LEFT)
    total_amount_var = tk.StringVar(value=f"{total_amount:.2f}")
    ttk.Label(total_frame, textvariable=total_amount_var, font=('微软雅黑', 11, 'bold'), foreground='red').pack(side=tk.LEFT, padx=5)

    ttk.Label(total_frame, text="已付金额:", font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=(15, 0))
    total_paid_var = tk.StringVar(value=f"{total_paid:.2f}")
    ttk.Label(total_frame, textvariable=total_paid_var, font=('微软雅黑', 11, 'bold')).pack(side=tk.LEFT, padx=5)

    ttk.Label(total_frame, text="未支付金额:", font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=(15, 0))
    total_debt_var = tk.StringVar(value=f"{total_debt:.2f}")
    ttk.Label(total_frame, textvariable=total_debt_var, font=('微软雅黑', 11, 'bold'), foreground='blue').pack(side=tk.LEFT, padx=5)
    
    # 更新总计信息显示函数
    def update_total_display():
        if is_kufang.get():
            total_frame.pack_forget()
        else:
            total_frame.pack(side=tk.LEFT, padx=(0, 20))
            total_quantity_var.set(f"{int(sum(item[3] for item in items))}")
            total_amount_var.set(f"{total_amount:.2f}")
            total_paid_var.set(f"{total_paid:.2f}")
            total_debt_var.set(f"{total_debt:.2f}")
    
    # 绑定复选框事件
    is_kufang.trace_add('write', lambda *args: update_total_display())
    # 初始化总计信息显示
    update_total_display()
    
    # 添加库房视图复选框
    checkbox_frame = ttk.Frame(bottom)
    checkbox_frame.pack(side=tk.LEFT, padx=(0, 20))
    ttk.Checkbutton(checkbox_frame, text="库房视图", variable=is_kufang).pack(side=tk.LEFT)
    
    def do_export():
        from tkinter import filedialog

        # 准备订单详情数据
        order_data = {
            'order_no': order_no,
            'customer_name': cust_name,
            'customer_address': cust_addr,
            'customer_phone': cust[3] if cust else '',
            'outbound_date': order[7][:10],
            'logistics': logistics or '',
            'show_kufang': is_kufang.get(),
            'total_quantity': int(sum(item[3] for item in items)),
            'total_amount': total_amount,
            'total_paid': total_paid,
            'total_debt': total_debt,
            'remark': order[8] if len(order) > 8 else "无"
        }

        # 准备产品明细数据
        product_data = []
        for idx, item in enumerate(items, 1):
            inv = dbutil.get_inventory_by_id(item[2])
            product_no = inv[2] if inv else ''
            color = inv[4] if inv else ''
            unit = inv[5] if inv else ''
            size = inv[3] if inv else ''
            quantity = item[3]
            price = item[4] if len(item) > 4 else 0.0
            amount = item[5] if len(item) > 5 else 0.0
            # 备注字段，数据库如有可填，否则留空
            # 去除每一项备注
            remark = ""
            product_data.append({
                'idx': idx,
                'product_no': product_no,
                'color': color,
                'unit': unit,
                'size': size,
                'quantity': quantity,
                'price': price,
                'amount': amount,
                'remark': remark
            })

        # 使用PDFUtil工具类生成订单详情PDF
        if PDFUtil.create_order_detail_pdf(order_data, product_data, cust):
            tk.messagebox.showinfo("导出成功", "PDF已成功导出！")

    def update_view():
        show_kufang = is_kufang.get()
        show_cols = ["idx", "product_no", "color", "unit", "size", "quantity"]
        if not show_kufang:
            show_cols += ["price", "amount"]
        tree['displaycolumns'] = show_cols
        for w in bottom.pack_slaves():
            w.pack_forget()
        # 重新添加备注信息显示
        remark_frame = ttk.Frame(bottom)
        remark_frame.pack(fill=tk.X, padx=0, pady=(0, 10))
        ttk.Label(remark_frame, text="备注信息:", font=('微软雅黑', 11)).pack(side=tk.LEFT)
        remark = order[8] if len(order) > 8 else "无"
        ttk.Label(remark_frame, text=remark, font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=5)

        chk.pack(side=tk.RIGHT, padx=(0, 12))
        btn_export.pack(side=tk.RIGHT, padx=(0, 12))
        ttk.Label(bottom, text=f"总计数量: {int(sum(item[3] for item in items))}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
        if not show_kufang:
            ttk.Label(bottom, text=f"总计金额: {total_amount:.2f}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
            ttk.Label(bottom, text=f"已付金额: {total_paid:.2f}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
            ttk.Label(bottom, text=f"未支付金额: {total_debt:.2f}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))

    btn_export = ttk.Button(bottom, text="导出出库单", width=14, command=do_export)
    chk = ttk.Checkbutton(bottom, text="库房出库单", variable=is_kufang, command=update_view)
    update_view()