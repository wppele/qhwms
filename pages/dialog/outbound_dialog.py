import tkinter as tk
from tkinter import ttk, messagebox
from util import dbutil
import datetime

def OutboundDialog(parent, cart_list, customer_name=None):
    dialog = tk.Toplevel(parent)
    dialog.title("出库单")
    w, h = 950, 560
    sw = dialog.winfo_screenwidth()
    sh = dialog.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    dialog.geometry(f"{w}x{h}+{x}+{y}")
    dialog.transient(parent)
    dialog.grab_set()
    now = datetime.datetime.now()
    # 顶部标题
    tk.Label(dialog, text="千辉鞋业出库单", font=("微软雅黑", 16, "bold"), fg="#2a5d2a").pack(pady=(18, 8))
    # 订单号、客户、出库日期一行显示
    top_row = ttk.Frame(dialog)
    top_row.pack(fill=tk.X, padx=30, pady=2)
    ttk.Label(top_row, text="订单号:", font=("微软雅黑", 11)).pack(side=tk.LEFT)
    order_no_var = tk.StringVar(value="")
    order_no_entry = ttk.Entry(top_row, textvariable=order_no_var, width=18, state='readonly')
    order_no_entry.pack(side=tk.LEFT, padx=4)
    ttk.Label(top_row, text="客户:", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(12,0))
    customers = dbutil.get_all_customers()
    customer_names = [c[1] for c in customers]
    customer_var = tk.StringVar()
    if customer_name:
        customer_var.set(customer_name)
    customer_combo = ttk.Combobox(top_row, textvariable=customer_var, values=customer_names, width=14, state="normal")
    customer_combo.pack(side=tk.LEFT, padx=4)
    if customer_name:
        customer_combo.set(customer_name)
    def on_customer_input(event):
        value = customer_var.get()
        value = value.strip().lower()
        if value == '':
            customer_combo['values'] = customer_names
            return
        filtered = [name for name in customer_names if value in name.lower()]
        customer_combo['values'] = filtered if filtered else customer_names
        if filtered:
            customer_combo.event_generate('<Down>')
    customer_combo.bind('<KeyRelease>', on_customer_input)
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
        detail_columns = ("product_no", "color","unit", "size", "quantity", "price", "amount")
        detail_headers = [
            ("product_no", "货号"),
            ("color", "颜色"),
            ("unit", "单位"),
            ("size", "尺码"),
            ("quantity", "数量"),
            ("price", "单价"),
            ("amount", "总计")
        ]
        detail_tree = ttk.Treeview(win, columns=detail_columns, show="headings", height=10)
        for col, text in detail_headers:
            detail_tree.heading(col, text=text)
            detail_tree.column(col, anchor=tk.CENTER, width=100)
        detail_tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
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
                unit = inv[5] if inv else ''
                size = inv[3] if inv else ''
                quantity = item[3]
                price = item[4] if len(item) > 4 else 0.0
                amount = item[6] if len(item) > 5 else 0.0
                detail_tree.insert('', tk.END, values=(product_no, color, unit, size, quantity, f"{price:.2f}", f"{amount:.2f}"))
        tree.bind('<<TreeviewSelect>>', show_detail)
        for o in orders:
            tree.insert('', tk.END, values=(o[1], f"{o[3]:.2f}", f"{o[5]:.2f}", f"{o[6]:.2f}", o[7]))
        ttk.Button(win, text="关闭", command=win.destroy).pack(pady=8)
    ttk.Button(top_row, text="历史订单", command=show_history).pack(side=tk.LEFT, padx=(8,0))
    ttk.Label(top_row, text="出库日期:", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(12,0))
    date_var = tk.StringVar(value=now.strftime('%Y-%m-%d'))
    ttk.Entry(top_row, textvariable=date_var, width=12, state='readonly').pack(side=tk.LEFT, padx=4)
    # 表格区
    columns = ("product_no", "color", "unit", "size", "quantity", "price", "amount", "item_pay_status", "paid_amount", "debt_amount", "product_id")
    headers = [
        ("product_no", "货号"),      # 0
        ("color", "颜色"),           # 1
        ("unit", "单位"),            # 2
        ("size", "尺码"),            # 3
        ("quantity", "数量"),        # 4
        ("price", "单价"),           # 5
        ("amount", "金额"),          # 6
        ("item_pay_status", "支付状态"), # 7
        ("paid_amount", "已付"),     # 8
        ("debt_amount", "待付款")    # 9
    ]
    tree = ttk.Treeview(dialog, columns=columns, show="headings", height=13)
    tree.pack(fill=tk.X, padx=30, pady=12)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=90)
    # 隐藏 product_id 列
    tree['displaycolumns'] = [col for col, _ in headers]
    # 填充表格，cart_list: [(inv_row, qty, price)]，inv_row[0]=product_id
    if cart_list:
        for v, qty, price in cart_list:
            inv = dbutil.get_inventory_by_id(v[0])
            product_no = inv[2] if inv else ''      # 0
            color = inv[4] if inv else ''           # 1
            unit = inv[5] if inv else ''            # 2
            size = inv[3] if inv else ''            # 3
            amount = qty * price                    # 6
            # values顺序严格对应columns
            tree.insert("", tk.END, values=(product_no, color, unit, size, qty, price, f"{amount:.2f}", "待付款", "0.00", f"{amount:.2f}", v[0]))

    # 新增：添加商品和删除商品按钮
    def add_item_row():
        all_inv = dbutil.get_all_inventory()
        display_items = [f"{inv[3]}-{inv[5]}-{inv[4]}" for inv in all_inv]
        values = ("", "", "", "", 0, 0.0, "0.00", "待付款", "0.00", "0.00", "")
        item_id = tree.insert("", tk.END, values=values)
        def edit_product_no():
            x, y, width, height = tree.bbox(item_id, '#1')
            entry = ttk.Combobox(tree, values=display_items, width=18)
            entry.place(x=x, y=y, width=width, height=height)
            entry.focus_set()
            def on_select(e=None):
                val = entry.get()
                inv = next((i for i in all_inv if f"{i[3]}-{i[5]}-{i[4]}" == val), None)
                product_no = inv[3] if inv else ''
                color = inv[5] if inv else ''
                unit = inv[6] if inv else ''
                size = inv[4] if inv else ''
                pid = inv[0] if inv else ''
                vals = list(tree.item(item_id)['values'])
                vals[0] = product_no   # 货号
                vals[1] = color        # 颜色
                vals[2] = unit         # 单位
                vals[3] = size         # 尺码
                vals[10] = pid         # product_id
                tree.item(item_id, values=vals)
                entry.destroy()
            def on_keyrelease(event):
                value = entry.get().strip().lower()
                if value == '':
                    entry['values'] = display_items
                elif len(value) >= 3:
                    filtered = [item for item in display_items if value in item.lower()]
                    entry['values'] = filtered if filtered else display_items
                    if filtered:
                        entry.event_generate('<Down>')
            entry.bind('<Return>', on_select)
            entry.bind('<<ComboboxSelected>>', on_select)
            entry.bind('<KeyRelease>', on_keyrelease)
        edit_product_no()

    def delete_selected_row():
        sel = tree.selection()
        for item in sel:
            tree.delete(item)
        calc_total()

    op_btn_frame = ttk.Frame(dialog)
    op_btn_frame.pack(fill=tk.X, padx=30, pady=2)
    ttk.Button(op_btn_frame, text="添加商品", command=add_item_row).pack(side=tk.LEFT)
    ttk.Button(op_btn_frame, text="删除选中", command=delete_selected_row).pack(side=tk.LEFT, padx=8)
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
                amount = float(vals[6]) if vals[6] else 0  # 修正为第7列
                paid = float(vals[8]) if vals[8] else 0
                debt = float(vals[9]) if vals[9] else 0
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
    # 允许编辑货号、尺码、数量、单价
    def on_double_click(event):
        item = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not item or col not in ('#1', '#4', '#5', '#6'):
            return
        if col == '#1':
            all_inv = dbutil.get_all_inventory()
            display_items = [f"{inv[3]}-{inv[5]}-{inv[4]}" for inv in all_inv]
            x, y, width, height = tree.bbox(item, col)
            value = tree.set(item, 'product_no')
            color = tree.set(item, 'color')
            size = tree.set(item, 'size')
            combo_value = f"{value}-{color}-{size}" if value else ""
            entry = ttk.Combobox(tree, values=display_items, width=18)
            entry.place(x=x, y=y, width=width, height=height)
            entry.set(combo_value)
            entry.focus_set()
            def on_select(e=None):
                val = entry.get()
                inv = next((i for i in all_inv if f"{i[3]}-{i[5]}-{i[4]}" == val), None)
                product_no = inv[3] if inv else ''
                color = inv[5] if inv else ''
                unit = inv[6] if inv else ''
                size = inv[4] if inv else ''
                pid = inv[0] if inv else ''
                vals = list(tree.item(item)['values'])
                vals[0] = product_no
                vals[1] = color
                vals[2] = unit
                vals[3] = size
                vals[10] = pid
                tree.item(item, values=vals)
                entry.destroy()
            def on_keyrelease(event):
                value = entry.get().strip().lower()
                if value == '':
                    entry['values'] = display_items
                elif len(value) >= 2:
                    filtered = [item for item in display_items if value in item.lower()]
                    entry['values'] = filtered if filtered else display_items
                    if filtered:
                        entry.event_generate('<Down>')
            entry.bind('<Return>', on_select)
            entry.bind('<<ComboboxSelected>>', on_select)
            entry.bind('<KeyRelease>', on_keyrelease)
        else:
            # 只允许编辑数量、单价、金额三列，且字段与列号严格对应
            editable_cols = ['#5', '#6', '#7']  # 数量、单价、金额
            col_names = {'#5': 4, '#6': 5, '#7': 6}  # 列号对应values索引
            if col not in editable_cols:
                return
            def edit_entry_by_col(item, col):
                col_idx = col_names[col]
                x, y, width, height = tree.bbox(item, col)
                vals = list(tree.item(item)['values'])
                value = vals[col_idx]
                entry = ttk.Entry(tree, width=8)
                entry.insert(0, value)
                entry.place(x=x, y=y, width=width, height=height)
                entry.focus_set()
                entry.selection_range(0, tk.END)
                def save_and_next(next_col=None):
                    new_val = entry.get()
                    vals = list(tree.item(item)['values'])
                    vals[col_idx] = new_val
                    # 自动计算金额和待付款
                    try:
                        qty = float(vals[4]) if vals[4] else 0      # 数量
                        price = float(vals[5]) if vals[5] else 0    # 单价
                        amount = qty * price                        # 金额
                        vals[6] = f"{amount:.2f}"
                        paid = float(vals[8]) if vals[8] else 0     # 已付
                        debt = amount - paid                        # 待付款
                        vals[9] = f"{debt:.2f}"
                    except Exception:
                        vals[6] = ""
                        vals[9] = ""
                    tree.item(item, values=vals)
                    entry.destroy()
                    calc_total()
                    if next_col:
                        tree.after(10, lambda: edit_entry_by_col(item, next_col))
                def on_focus_out(e):
                    save_and_next()
                def on_return(e):
                    save_and_next()
                def on_tab(e):
                    next_idx = editable_cols.index(col) + 1
                    if next_idx < len(editable_cols):
                        next_col = editable_cols[next_idx]
                        save_and_next(next_col)
                    else:
                        save_and_next()
                    return "break"
                entry.bind('<FocusOut>', on_focus_out)
                entry.bind('<Return>', on_return)
                entry.bind('<Tab>', on_tab)
            edit_entry_by_col(item, col)
    tree.bind('<Double-1>', on_double_click)
    # 初始合计
    calc_total()
    # 物流信息单独一行显示在保存按钮上方
    # 已在上方 logistics_row 实现
    # 底部按钮
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=18)

    def on_submit():
        # 1. 检测客户姓名
        if not customer_var.get():
            messagebox.showwarning("提示", "请选择客户！")
            return
        # 2. 检查每行商品数量和单价不能为0，且库存是否充足
        for item in tree.get_children():
            vals = tree.item(item)['values']
            product_id = vals[10]  # product_id
            quantity = int(vals[4]) if vals[4] else 0
            price = float(vals[5]) if vals[5] else 0
            product_no = vals[0]
            color = vals[1]
            size = vals[3]
            if quantity <= 0:
                messagebox.showerror("错误", f"货号:{product_no} 颜色:{color} 尺码:{size} 数量不能为0！")
                return
            if price <= 0:
                messagebox.showerror("错误", f"货号:{product_no} 颜色:{color} 尺码:{size} 单价不能为0！")
                return
            inv = dbutil.get_inventory_by_id(product_id)
            stock_qty = inv[-1] if inv else 0
            if quantity > stock_qty:
                messagebox.showerror("库存不足", f"货号:{product_no} 颜色:{color} 尺码:{size} 库存仅剩{stock_qty}，无法出库{quantity}件！")
                return
        # 3. 计算已付金额和待付金额（如填写了本次支付金额，则自动分配到各商品）
        pay_amount = pay_amount_var.get()
        try:
            pay_amount = float(pay_amount)
        except Exception:
            pay_amount = 0.0
        # 自动分配支付金额到各商品
        if pay_amount > 0:
            # 按待付款升序分配
            items = []
            for tree_id in tree.get_children():
                vals = tree.item(tree_id)['values']
                amount = float(vals[6]) if vals[6] else 0  # 金额
                paid = float(vals[8]) if vals[8] else 0    # 已付
                debt = float(vals[9]) if vals[9] else 0    # 待付款
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
                vals[7] = new_status
                vals[8] = f"{new_paid:.2f}"
                vals[9] = f"{new_debt:.2f}"
                tree.item(item['tree_id'], values=vals)
                remain -= pay_this
            calc_total()
        total_paid = float(total_paid_var.get())
        total_debt = float(total_debt_var.get())
        # 4. 生成订单号
        if not order_no_var.get():
            today_str = now.strftime('%Y%m%d')
            all_orders = dbutil.get_all_outbound_orders()
            today_orders = [o for o in all_orders if o[1].startswith(f"QH{today_str}")]
            order_seq = len(today_orders) + 1
            order_no = f"QH{today_str}{order_seq:04d}"
            order_no_var.set(order_no)
            order_no_entry.update()
        # 5. 生成出库单（写入数据库）
        try:
            total = float(total_var.get())
            now_str = now.strftime('%Y-%m-%d %H:%M:%S')
            # 获取客户id
            customer_id = None
            for c in customers:
                if c[1] == customer_var.get():
                    customer_id = c[0]
                    break
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
                product_id = vals[10]  # product_id
                quantity = int(vals[4]) if vals[4] else 0
                price = float(vals[5]) if vals[5] else 0
                amount = float(vals[6]) if vals[6] else 0
                item_pay_status = 1 if vals[7] == '已付' else 0
                paid_amount = float(vals[8]) if vals[8] else 0
                debt_amount = float(vals[9]) if vals[9] else 0
                returnable_qty = quantity
                dbutil.insert_outbound_item(
                    outbound_id, product_id, quantity, price, amount, item_pay_status, paid_amount, debt_amount, returnable_qty
                )
                dbutil.update_inventory_size_by_id(product_id, size)
                item_ids.append(str(idx+1))
                dbutil.decrease_inventory_by_id(product_id, quantity)
            if total_debt > 0:
                dbutil.insert_debt_record(outbound_id, ','.join(item_ids), total_debt)
            if total_paid > 0:
                dbutil.insert_payment_record(outbound_id, ','.join(item_ids), total_paid, now_str, pay_method_var.get())
        except Exception as e:
            messagebox.showerror("错误", f"保存出库单失败：{e}")
            return
        # 6. 提示是否输出为PDF
        if messagebox.askyesno("出库单已保存", "是否输出为PDF？"):
            try:
                from pages.dialog.outbound_detail_dialog import show_outbound_detail
                show_outbound_detail(None, order_no)
            except Exception as e:
                messagebox.showerror("错误", f"打开出库单详情失败：{e}")
        # 自动删除暂存单（如有）
        # 判断是否为暂存单进入（cart_list不为空且customer_name不为空）
        if cart_list and customer_name:
            # 查找暂存单id
            # 通过客户名、金额、时间等条件查找最近的draft_order
            all_drafts = dbutil.get_all_draft_orders()
            match_id = None
            for d in all_drafts:
                # d: (draft_id, customer_id, total_amount, remark, create_time)
                cust = dbutil.get_customer_by_id(d[1])
                if cust and cust[1] == customer_name and abs(d[2] - total) < 0.01:
                    match_id = d[0]
                    break
            if match_id:
                dbutil.delete_draft_order(match_id)
        if hasattr(parent, 'refresh') and callable(parent.refresh):
            parent.refresh()
        dialog.destroy()

    def on_save_draft():
        # 检查客户
        if not customer_var.get():
            messagebox.showwarning("提示", "请选择客户！")
            return
        # 暂存时写入draft_order和draft_item表
        try:
            total = float(total_var.get())
            now_str = now.strftime('%Y-%m-%d %H:%M:%S')
            # 获取客户id
            customer_id = None
            for c in customers:
                if c[1] == customer_var.get():
                    customer_id = c[0]
                    break
            remark = ''
            draft_id = dbutil.insert_draft_order(customer_id, total, remark, now_str)
            for item in tree.get_children():
                vals = tree.item(item)['values']
                product_id = vals[10]  # product_id
                quantity = int(vals[4]) if vals[4] else 0
                price = float(vals[5]) if vals[5] else 0
                amount = float(vals[6]) if vals[6] else 0
                dbutil.insert_draft_item(draft_id, product_id, quantity, price, amount)
            messagebox.showinfo("暂存成功", "出库单已暂存，可在库存页面查看和继续操作！")
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"暂存失败：{e}")
            return

    ttk.Button(btn_frame, text="暂存出库单", command=on_save_draft, width=16).pack(side=tk.LEFT, padx=8)
    ttk.Button(btn_frame, text="生成出库单", command=on_submit, width=16).pack(side=tk.LEFT, padx=8)

    dialog.wait_window()
