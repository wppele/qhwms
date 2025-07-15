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
    # 历史订单按钮
    def show_history():
        name = customer_var.get()
        cust = next((c for c in customers if c[1] == name), None)
        if not cust:
            messagebox.showinfo("提示", "请先选择客户")
            return
        cid = cust[0]
        orders = [o for o in dbutil.get_all_outbound_orders() if o[2] == cid]
        win = tk.Toplevel(dialog)
        win.title(f"{name} 历史订单")
        win.geometry("1100x500")
        ttk.Label(win, text=f"客户：{name}  共{len(orders)}单", font=("微软雅黑", 12, "bold")).pack(pady=8)
        columns = ("order_no", "total_amount", "total_paid", "total_debt", "create_time")
        headers = [
            ("order_no", "订单号"),
            ("total_amount", "总金额"),
            ("total_paid", "已付"),
            ("total_debt", "待付款"),
            ("create_time", "出库日期")
        ]
        tree = ttk.Treeview(win, columns=columns, show="headings", height=8)
        for col, text in headers:
            tree.heading(col, text=text)
            tree.column(col, anchor=tk.CENTER, width=120)
        tree.pack(fill=tk.X, padx=16, pady=4)
        # 明细表
        detail_columns = ("product_no", "color", "quantity", "price", "amount")
        detail_headers = [
            ("product_no", "货号"),
            ("color", "颜色"),
            ("quantity", "数量"),
            ("price", "单价"),
            ("amount", "总计")
        ]
        detail_tree = ttk.Treeview(win, columns=detail_columns, show="headings", height=10)
        for col, text in detail_headers:
            detail_tree.heading(col, text=text)
            detail_tree.column(col, anchor=tk.CENTER, width=100)
        detail_tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        # 订单选择事件
        def show_detail(event):
            for i in detail_tree.get_children():
                detail_tree.delete(i)
            sel = tree.selection()
            if not sel:
                return
            idx = tree.index(sel[0])
            order = orders[idx]
            items = dbutil.get_outbound_items_by_order(order[0])
            for item in items:
                inv = dbutil.get_inventory_by_id(item[2])
                product_no = inv[2] if inv else ''
                color = inv[4] if inv else ''
                quantity = item[3]
                amount = item[4]
                price = amount / quantity if quantity else 0.0
                detail_tree.insert('', tk.END, values=(product_no, color, quantity, f"{price:.2f}", f"{amount:.2f}"))
        tree.bind('<<TreeviewSelect>>', show_detail)
        for o in orders:
            tree.insert('', tk.END, values=(o[1], f"{o[3]:.2f}", f"{o[5]:.2f}", f"{o[6]:.2f}", o[7]))
        ttk.Button(win, text="关闭", command=win.destroy).pack(pady=8)
    ttk.Button(top_row, text="历史订单", command=show_history).pack(side=tk.LEFT, padx=(8,0))
    ttk.Label(top_row, text="出库日期:", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(12,0))
    date_var = tk.StringVar(value=now.strftime('%Y-%m-%d'))
    ttk.Entry(top_row, textvariable=date_var, width=12, state='readonly').pack(side=tk.LEFT, padx=4)
    # 表格区
    columns = ("product_no", "color", "quantity", "price", "amount", "item_pay_status", "paid_amount", "debt_amount", "product_id")
    headers = [
        ("product_no", "货号"),
        ("color", "颜色"),
        ("quantity", "数量"),
        ("price", "单价"),
        ("amount", "金额"),
        ("item_pay_status", "支付状态"),
        ("paid_amount", "已付"),
        ("debt_amount", "待付款")
    ]
    tree = ttk.Treeview(dialog, columns=columns, show="headings", height=13)
    tree.pack(fill=tk.X, padx=30, pady=12)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=90)
    # 填充表格，cart_list: [(inv_row, qty, price)]，inv_row[0]=product_id
    for v, qty, price in cart_list:
        inv = dbutil.get_inventory_by_id(v[0])
        product_no = inv[2] if inv else ''
        color = inv[4] if inv else ''
        amount = qty * price
        tree.insert("", tk.END, values=(product_no, color, qty, price, f"{amount:.2f}", "待付款", "0.00", f"{amount:.2f}", v[0]))
    # 合计金额、总已付、总待付款一行显示在表格下方
    bottom_frame = ttk.Frame(dialog)
    bottom_frame.pack(fill=tk.X, padx=30, pady=8)
    ttk.Label(bottom_frame, text="合计金额:", font=("微软雅黑", 11)).pack(side=tk.LEFT)
    total_var = tk.StringVar(value="0.00")
    ttk.Entry(bottom_frame, textvariable=total_var, width=12, state='readonly').pack(side=tk.LEFT, padx=6)
    ttk.Label(bottom_frame, text="总已付:", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(18,0))
    total_paid_var = tk.StringVar(value="0.00")
    ttk.Entry(bottom_frame, textvariable=total_paid_var, width=12, state='readonly').pack(side=tk.LEFT, padx=6)
    ttk.Label(bottom_frame, text="总待付款:", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(18,0))
    total_debt_var = tk.StringVar(value="0.00")
    ttk.Entry(bottom_frame, textvariable=total_debt_var, width=12, state='readonly').pack(side=tk.LEFT, padx=6)

    # 新增：本次支付金额输入和支付方式选择
    pay_frame = ttk.Frame(dialog)
    pay_frame.pack(fill=tk.X, padx=30, pady=2)
    ttk.Label(pay_frame, text="本次支付金额:", font=("微软雅黑", 11)).pack(side=tk.LEFT)
    pay_amount_var = tk.StringVar()
    ttk.Entry(pay_frame, textvariable=pay_amount_var, width=14).pack(side=tk.LEFT, padx=6)
    ttk.Label(pay_frame, text="支付方式:", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(18,0))
    pay_method_var = tk.StringVar(value="现金")
    pay_method_combo = ttk.Combobox(pay_frame, textvariable=pay_method_var, values=["现金", "微信", "支付宝", "银联", "云闪付", "其他"], width=8, state="readonly")
    pay_method_combo.pack(side=tk.LEFT, padx=6)
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

    def save_order():
        # 校验
        if not customer_var.get():
            messagebox.showwarning("提示", "请选择客户！")
            return False, None
        try:
            total = float(total_var.get())
            now_str = now.strftime('%Y-%m-%d %H:%M:%S')
            # 获取客户id
            customer_id = None
            for c in customers:
                if c[1] == customer_var.get():
                    customer_id = c[0]
                    break
            # 合计
            total_paid = float(total_paid_var.get())
            total_debt = float(total_debt_var.get())
            # pay_status
            if total_debt <= 0:
                pay_status = 2  # 全额
            elif total_paid > 0 and total_debt > 0:
                pay_status = 1  # 部分
            else:
                pay_status = 0  # 未支付
            outbound_id = dbutil.insert_outbound_order(
                order_no_var.get(), customer_id, total, pay_status, total_paid, total_debt, now_str
            )
            item_ids = []
            for idx, item in enumerate(tree.get_children()):
                vals = tree.item(item)['values']
                product_id = vals[9]  # 新增列
                quantity = int(vals[3])
                amount = float(vals[5]) if vals[5] else 0
                item_pay_status = 1 if vals[6] == '已付' else 0
                paid_amount = float(vals[7]) if vals[7] else 0
                debt_amount = float(vals[8]) if vals[8] else 0
                returnable_qty = quantity
                dbutil.insert_outbound_item(
                    outbound_id, product_id, quantity, amount, item_pay_status, paid_amount, debt_amount, returnable_qty
                )
                item_ids.append(str(idx+1))
                dbutil.decrease_inventory_by_id(product_id, quantity)
            # 写入debt_record
            if total_debt > 0:
                dbutil.insert_debt_record(outbound_id, ','.join(item_ids), total_debt)
            # 写入payment_record（如有支付金额）
            if total_paid > 0:
                dbutil.insert_payment_record(outbound_id, ','.join(item_ids), total_paid, now_str, pay_method_var.get())
            return True, None
        except Exception as e:
            messagebox.showerror("错误", f"保存出库单失败：{e}")
            return False, None

    def on_submit():
        ok, _ = save_order()
        if ok:
            if hasattr(parent, 'cart_count'):
                try:
                    parent.cart_count.set(0)
                except Exception:
                    pass
            if hasattr(parent, 'refresh') and callable(parent.refresh):
                parent.refresh()
            messagebox.showinfo("成功", "出库单已保存！")
            dialog.destroy()

    def on_submit_and_pay():
        try:
            pay_amount = float(pay_amount_var.get())
            if pay_amount <= 0:
                messagebox.showwarning("提示", "请输入大于0的支付金额！")
                return
        except Exception:
            messagebox.showwarning("提示", "请输入有效的支付金额！")
            return
        # 仅UI层分配支付金额，不写数据库
        # 获取所有明细，按待付款升序分配
        items = []
        for tree_id in tree.get_children():
            vals = tree.item(tree_id)['values']
            amount = float(vals[5]) if vals[5] else 0
            paid = float(vals[7]) if vals[7] else 0
            debt = float(vals[8]) if vals[8] else 0
            items.append({'tree_id': tree_id, 'amount': amount, 'paid': paid, 'debt': debt})
        items.sort(key=lambda x: x['debt'])
        remain = pay_amount
        for item in items:
            if item['debt'] <= 0:
                continue
            if remain <= 0:
                break
            pay_this = min(remain, item['debt'])
            new_paid = item['paid'] + pay_this
            new_debt = item['debt'] - pay_this
            new_status = '已付' if new_debt <= 0.01 else '待付款'
            vals = list(tree.item(item['tree_id'])['values'])
            vals[6] = new_status
            vals[7] = f"{new_paid:.2f}"
            vals[8] = f"{new_debt:.2f}"
            tree.item(item['tree_id'], values=vals)
            remain -= pay_this
        calc_total()
        messagebox.showinfo("成功", f"已结账，实际支付：{pay_amount - remain:.2f} 元\n如需关闭请点击“生成出库单”")

    ttk.Button(btn_frame, text="生成出库单", command=on_submit, width=16).pack(side=tk.LEFT, padx=8)
    ttk.Button(btn_frame, text="保存并结账", command=on_submit_and_pay, width=16).pack(side=tk.LEFT, padx=8)
    dialog.wait_window()
