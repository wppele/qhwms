import tkinter as tk
from tkinter import ttk, messagebox
from util import dbutil
import datetime

def OutboundDialog(parent, cart_list):
    dialog = tk.Toplevel(parent)
    dialog.title("出库单")
    # 居中显示
    w, h = 950, 560
    sw = dialog.winfo_screenwidth()
    sh = dialog.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    dialog.geometry(f"{w}x{h}+{x}+{y}")
    dialog.transient(parent)
    dialog.grab_set()
    # 顶部标题
    tk.Label(dialog, text="千辉鞋业出库单", font=("微软雅黑", 16, "bold"), fg="#2a5d2a").pack(pady=(18, 8))
    # 订单号、客户、出库日期一行显示
    now = datetime.datetime.now()
    order_no = f"QH{now.strftime('%Y%m%d%H%M%S')}"
    top_row = ttk.Frame(dialog)
    top_row.pack(fill=tk.X, padx=30, pady=2)
    ttk.Label(top_row, text="订单号:", font=("微软雅黑", 11)).pack(side=tk.LEFT)
    order_no_var = tk.StringVar(value=order_no)
    ttk.Entry(top_row, textvariable=order_no_var, width=18, state='readonly').pack(side=tk.LEFT, padx=4)
    ttk.Label(top_row, text="客户:", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(12,0))
    customers = dbutil.get_all_customers()
    customer_names = [c[1] for c in customers]
    customer_var = tk.StringVar()
    customer_combo = ttk.Combobox(top_row, textvariable=customer_var, values=customer_names, width=14, state="readonly")
    customer_combo.pack(side=tk.LEFT, padx=4)
    ttk.Label(top_row, text="出库日期:", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(12,0))
    date_var = tk.StringVar(value=now.strftime('%Y-%m-%d'))
    ttk.Entry(top_row, textvariable=date_var, width=12, state='readonly').pack(side=tk.LEFT, padx=4)
    # 表格区
    columns = ("product_no", "color", "size", "quantity", "price", "amount", "item_pay_status", "paid_amount", "debt_amount")
    headers = [
        ("product_no", "货号"),
        ("color", "颜色"),
        ("size", "尺码"),
        ("quantity", "数量"),
        ("price", "单价"),
        ("amount", "金额"),
        ("item_pay_status", "支付状态"),
        ("paid_amount", "已付"),
        ("debt_amount", "欠款")
    ]
    tree = ttk.Treeview(dialog, columns=columns, show="headings", height=13)
    tree.pack(fill=tk.X, padx=30, pady=12)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=90)
    # 填充表格
    for v, qty, price in cart_list:
        amount = qty * price
        tree.insert("", tk.END, values=(v[2], v[4], v[3], qty, price, f"{amount:.2f}", "欠款", "0.00", f"{amount:.2f}"))
    # 合计金额、总已付、总欠款一行显示在表格下方
    bottom_frame = ttk.Frame(dialog)
    bottom_frame.pack(fill=tk.X, padx=30, pady=8)
    ttk.Label(bottom_frame, text="合计金额:", font=("微软雅黑", 11)).pack(side=tk.LEFT)
    total_var = tk.StringVar(value="0.00")
    ttk.Entry(bottom_frame, textvariable=total_var, width=12, state='readonly').pack(side=tk.LEFT, padx=6)
    ttk.Label(bottom_frame, text="总已付:", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(18,0))
    total_paid_var = tk.StringVar(value="0.00")
    ttk.Entry(bottom_frame, textvariable=total_paid_var, width=12, state='readonly').pack(side=tk.LEFT, padx=6)
    ttk.Label(bottom_frame, text="总欠款:", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(18,0))
    total_debt_var = tk.StringVar(value="0.00")
    ttk.Entry(bottom_frame, textvariable=total_debt_var, width=12, state='readonly').pack(side=tk.LEFT, padx=6)
    # 自动合计金额
    def calc_total():
        total = 0.0
        total_paid = 0.0
        total_debt = 0.0
        for item in tree.get_children():
            vals = tree.item(item)['values']
            try:
                amount = float(vals[5]) if vals[5] else 0
                paid = float(vals[7]) if vals[7] else 0
                debt = float(vals[8]) if vals[8] else 0
                total += amount
                total_paid += paid
                total_debt += debt
                tree.set(item, "amount", f"{amount:.2f}")
            except Exception:
                tree.set(item, "amount", "")
        total_var.set(f"{total:.2f}")
        total_paid_var.set(f"{total_paid:.2f}")
        total_debt_var.set(f"{total_debt:.2f}")
    # 监听单价输入
    def on_price_edit(event):
        for item in tree.get_children():
            vals = tree.item(item)['values']
            price = vals[4]
            if not price:
                continue
            try:
                float(price)
            except Exception:
                tree.set(item, "price", "")
        calc_total()
    # 允许编辑单价
    def on_double_click(event):
        item = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not item or col != '#5':
            return
        x, y, width, height = tree.bbox(item, col)
        value = tree.set(item, "price")
        entry = ttk.Entry(tree, width=8)
        entry.insert(0, value)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()
        def on_focus_out(e):
            tree.set(item, "price", entry.get())
            entry.destroy()
            calc_total()
        entry.bind('<FocusOut>', on_focus_out)
        entry.bind('<Return>', on_focus_out)
    tree.bind('<Double-1>', on_double_click)
    # 初始合计
    calc_total()
    # 物流信息单独一行显示在保存按钮上方
    # 已在上方 logistics_row 实现
    # 底部按钮
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=18)
    def on_submit():
        # 校验
        if not customer_var.get():
            messagebox.showwarning("提示", "请选择客户！")
            return
        # 生成出库单主表
        try:
            total = float(total_var.get())
            total_paid = float(total_paid_var.get())
            total_debt = float(total_debt_var.get())
            now_str = now.strftime('%Y-%m-%d %H:%M:%S')
            # 获取客户id
            customer_id = None
            for c in customers:
                if c[1] == customer_var.get():
                    customer_id = c[0]
                    break
            outbound_id = dbutil.insert_outbound_order(
                order_no_var.get(), customer_id, total, 0, total_paid, total_debt, now_str
            )
            # 插入明细
            for idx, item in enumerate(tree.get_children()):
                vals = tree.item(item)['values']
                product_no = vals[0]
                color = vals[1]
                size = vals[2]
                quantity = int(vals[3])
                price = float(vals[4]) if vals[4] else 0
                amount = float(vals[5]) if vals[5] else 0
                item_pay_status = 0 # 欠款
                paid_amount = 0.0
                debt_amount = amount
                returnable_qty = quantity
                # 可扩展：后续支持明细级支付
                dbutil.insert_outbound_item(
                    outbound_id, None, product_no, color, size, quantity, amount, item_pay_status, paid_amount, debt_amount, returnable_qty
                )
                # 优先用库存主键id减少库存
                inventory_id = None
                for cart in cart_list:
                    v, qty, p = cart
                    if v[2] == product_no and v[4] == color and v[3] == size and qty == quantity:
                        inventory_id = v[0]
                        break
                if inventory_id:
                    dbutil.decrease_inventory_by_id(inventory_id, quantity)
                else:
                    dbutil.decrease_inventory(product_no, color, size, quantity)
            # 出库成功后清空待出库数量并刷新库存界面
            if hasattr(parent, 'cart_count'):
                try:
                    parent.cart_count.set(0)
                except Exception:
                    pass
            if hasattr(parent, 'refresh') and callable(parent.refresh):
                parent.refresh()
            messagebox.showinfo("成功", "出库单已保存！")
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存出库单失败：{e}")
    ttk.Button(btn_frame, text="生成出库单", command=on_submit, width=16).pack()
    dialog.wait_window()
