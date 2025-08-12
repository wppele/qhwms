import tkinter as tk
from tkinter import ttk, messagebox
from util import dbutil
import datetime

# 存储上次选择的商品
last_selected_product = ''

def OutboundDialog(parent, cart_list, customer_name=None):
    dialog = tk.Toplevel(parent)
    dialog.title("出库单")
    w, h = 950, 600
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
        
        columns = ("order_no", "total_amount", "create_time")
        headers = [
            ("order_no", "订单号"),
            ("total_amount", "总金额"),
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
                amount = item[6] if len(item) > 6 else 0.0
                detail_tree.insert('', tk.END, values=(product_no, color, unit, size, quantity, f"{price:.2f}", f"{amount:.2f}"))
        tree.bind('<<TreeviewSelect>>', show_detail)
        
        for o in orders:
            tree.insert('', tk.END, values=(o[1], f"{o[3]:.2f}", o[7]))
        
        ttk.Button(win, text="关闭", command=win.destroy).pack(pady=8)
    
    ttk.Button(top_row, text="历史订单", command=show_history).pack(side=tk.LEFT, padx=(8,0))
    
    ttk.Label(top_row, text="出库日期:", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(12,0))
    date_var = tk.StringVar(value=now.strftime('%Y-%m-%d'))
    ttk.Entry(top_row, textvariable=date_var, width=12, state='readonly').pack(side=tk.LEFT, padx=4)
    
    # 表格区 - 移除支付相关列
    columns = ("product_no", "color", "unit", "size", "quantity", "price", "amount", "product_id")
    headers = [
        ("product_no", "货号"),      # 0
        ("color", "颜色"),           # 1
        ("unit", "单位"),            # 2
        ("size", "尺码"),            # 3
        ("quantity", "数量"),        # 4
        ("price", "单价"),           # 5
        ("amount", "金额"),          # 6
    ]
    # 创建一个框架来放置 Treeview 和滚动条
    tree_frame = ttk.Frame(dialog)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=12)

    # 创建垂直滚动条
    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # 创建 Treeview 并关联滚动条
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=13, yscrollcommand=scrollbar.set)
    scrollbar.config(command=tree.yview)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=100)
    
    # 隐藏 product_id 列
    tree['displaycolumns'] = [col for col, _ in headers]
    
    # 填充表格，cart_list: [(inv_row, qty, price)]，inv_row[0]=product_id
    if cart_list:
        for v, qty, price in cart_list:
            inv = dbutil.get_inventory_by_id(v[0])
            product_no = inv[2] if inv else ''      # 0
            color = inv[3] if inv else ''           # 1
            unit = inv[4] if inv else ''            # 2
            size = inv[5] if inv else ''            # 3
            amount = qty * price                    # 6
            # values顺序严格对应columns
            tree.insert("", tk.END, values=(product_no, color, unit, size, qty, price, f"{amount:.2f}", v[0]))

    # 添加商品和删除商品按钮
    def add_item_row():
        # 打开商品搜索对话框
        from pages.dialog.search_dialog import ProductSearchDialog
        # 使用nonlocal关键字引用外部函数的dialog变量
        nonlocal dialog
        
        # 检查是否已有搜索对话框实例，如果有则显示它
        if hasattr(dialog, 'search_dialog') and dialog.search_dialog.winfo_exists():
            dialog.search_dialog.deiconify()
            return
        
        def on_product_selected(event=None):
            product = search_dialog.get_selected_product()
            if product:
                # 插入新行
                values = (
                    product['product_no'],
                    product['color'],
                    product['unit'],
                    product['size'],
                    0,  # 数量
                    0.0,  # 单价
                    "0.00",  # 金额
                    product['id']  # product_id
                )
                item_id = tree.insert("", tk.END, values=values)
                
                # 更新上次选择的商品
                global last_selected_product
                last_selected_product = f"{product['product_no']}-{product['unit']}-{product['color']}"
            
        search_dialog = ProductSearchDialog(dialog)
        # 保存对话框实例
        dialog.search_dialog = search_dialog
        search_dialog.bind('<<ProductSelected>>', on_product_selected)
        # 显示对话框
        search_dialog.deiconify()
            

    def delete_selected_row():
        sel = tree.selection()
        for item in sel:
            tree.delete(item)
        calc_total()

    op_btn_frame = ttk.Frame(dialog)
    op_btn_frame.pack(fill=tk.X, padx=30, pady=2)
    ttk.Button(op_btn_frame, text="添加商品", command=add_item_row).pack(side=tk.LEFT)
    ttk.Button(op_btn_frame, text="删除选中", command=delete_selected_row).pack(side=tk.LEFT, padx=8)
    
    # 合计金额、支付金额和余款金额
    bottom_frame = ttk.Frame(dialog)
    bottom_frame.pack(fill=tk.X, padx=30, pady=8)

    # 合计金额
    ttk.Label(bottom_frame, text="合计金额:", font=('微软雅黑', 11)).pack(side=tk.LEFT)
    total_var = tk.StringVar(value="0.00")
    ttk.Entry(bottom_frame, textvariable=total_var, width=12, state='readonly').pack(side=tk.LEFT, padx=6)

    # 支付金额
    ttk.Label(bottom_frame, text="支付金额:", font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=(12, 0))
    total_paid_var = tk.StringVar(value="0.00")
    total_paid_entry = ttk.Entry(bottom_frame, textvariable=total_paid_var, width=12)
    total_paid_entry.pack(side=tk.LEFT, padx=6)

    def on_paid_change(event=None):
        try:
            total = float(total_var.get())
            paid = float(total_paid_var.get()) if total_paid_var.get() else 0
            debt = total - paid
            total_debt_var.set(f"{debt:.2f}")
        except ValueError:
            total_debt_var.set("0.00")

    total_paid_entry.bind('<FocusOut>', on_paid_change)
    total_paid_entry.bind('<Return>', on_paid_change)

    # 余款金额
    ttk.Label(bottom_frame, text="余款金额:", font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=(12, 0))
    total_debt_var = tk.StringVar(value="0.00")
    ttk.Entry(bottom_frame, textvariable=total_debt_var, width=12, state='readonly').pack(side=tk.LEFT, padx=6)

    # 付款方式
    ttk.Label(bottom_frame, text="付款方式:", font=('微软雅黑', 11)).pack(side=tk.LEFT, padx=(12, 0))
    payment_methods = ['微信', '支付宝', '现金', '银联']
    pay_method_var = tk.StringVar(value=payment_methods[0])
    pay_method_combobox = ttk.Combobox(bottom_frame, textvariable=pay_method_var, values=payment_methods, width=10)
    pay_method_combobox.pack(side=tk.LEFT, padx=6)

    # 自动合计金额
    def calc_total():
        total = 0.0
        for item in tree.get_children():
            vals = tree.item(item)['values']
            try:
                amount = float(vals[6]) if vals[6] else 0  # 金额列
                total += amount
                tree.set(item, "amount", f"{amount:.2f}")
            except Exception:
                tree.set(item, "amount", "")
        total_var.set(f"{total:.2f}")
        on_paid_change()
    
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
            # 打开商品搜索对话框
            from pages.dialog.search_dialog import ProductSearchDialog
            # 使用nonlocal关键字引用外部函数的dialog变量
            nonlocal dialog
            
            # 检查是否已有搜索对话框实例，如果有则显示它
            if hasattr(dialog, 'search_dialog') and dialog.search_dialog.winfo_exists():
                dialog.search_dialog.deiconify()
                return
            
            def on_product_selected(event=None):
                product = search_dialog.get_selected_product()
                if product:
                    # 更新商品信息
                    vals = list(tree.item(item)['values'])
                    vals[0] = product['product_no']  # 货号
                    vals[1] = product['color']       # 颜色
                    vals[2] = product['unit']        # 单位
                    vals[3] = product['size']        # 尺码
                    vals[7] = product['id']          # product_id
                    tree.item(item, values=vals)
                    
                    # 更新上次选择的商品
                    global last_selected_product
                    last_selected_product = f"{product['product_no']}-{product['unit']}-{product['color']}"
            
            search_dialog = ProductSearchDialog(dialog)
            # 保存对话框实例
            dialog.search_dialog = search_dialog
            search_dialog.bind('<<ProductSelected>>', on_product_selected)
            # 显示对话框
            search_dialog.deiconify()
        else:
            # 只允许编辑数量、单价、尺码列
            editable_cols = ['#4', '#5', '#6']  # 尺码、数量、单价
            col_names = {'#4': 3, '#5': 4, '#6': 5}  # 列号对应values索引
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
                    # 自动计算金额
                    try:
                        qty = float(vals[4]) if vals[4] else 0      # 数量
                        price = float(vals[5]) if vals[5] else 0    # 单价
                        amount = qty * price                        # 金额
                        vals[6] = f"{amount:.2f}"
                    except Exception:
                        vals[6] = ""
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
                        # 同一行的下一列
                        next_col = editable_cols[next_idx]
                        save_and_next(next_col)
                    else:
                        # 获取当前项
                        current_item = tree.selection()[0]
                        # 获取当前项的索引
                        children = tree.get_children()
                        current_index = children.index(current_item)
                        # 检查是否有下一项
                        if current_index + 1 < len(children):
                            # 获取下一项
                            next_item = children[current_index + 1]
                            # 保存当前项的更改
                            save_and_next()
                            # 延迟编辑下一项的第一个可编辑列
                            tree.after(10, lambda: edit_entry_by_col(next_item, editable_cols[0]))
                        else:
                            # 没有下一项，保存当前项的更改
                            save_and_next()
                    return "break"
                
                def on_left(e):
                    prev_idx = editable_cols.index(col) - 1
                    if prev_idx >= 0:
                        prev_col = editable_cols[prev_idx]
                        save_and_next(prev_col)
                    return "break"

                def on_right(e):
                    next_idx = editable_cols.index(col) + 1
                    if next_idx < len(editable_cols):
                        next_col = editable_cols[next_idx]
                        save_and_next(next_col)
                    else:
                        # 同一行最后一列按右键，跳到下一行第一列
                        current_item = tree.selection()[0]
                        children = tree.get_children()
                        current_index = children.index(current_item)
                        if current_index + 1 < len(children):
                            next_item = children[current_index + 1]
                            save_and_next()
                            tree.after(10, lambda: edit_entry_by_col(next_item, editable_cols[0]))
                        else:
                            save_and_next()
                    return "break"

                def on_up(e):
                    current_item = tree.selection()[0]
                    children = tree.get_children()
                    current_index = children.index(current_item)
                    if current_index > 0:
                        prev_item = children[current_index - 1]
                        save_and_next()
                        # 确保选择上一行
                        tree.selection_set(prev_item)
                        tree.see(prev_item)
                        tree.after(10, lambda col=col: edit_entry_by_col(prev_item, col))
                    return "break"

                def on_down(e):
                    current_item = tree.selection()[0]
                    children = tree.get_children()
                    current_index = children.index(current_item)
                    if current_index + 1 < len(children):
                        next_item = children[current_index + 1]
                        save_and_next()
                        # 确保选择下一行
                        tree.selection_set(next_item)
                        tree.see(next_item)
                        tree.after(10, lambda col=col: edit_entry_by_col(next_item, col))
                    return "break"

                entry.bind('<FocusOut>', on_focus_out)
                entry.bind('<Return>', on_return)
                entry.bind('<Tab>', on_tab)
                entry.bind('<Left>', on_left)
                entry.bind('<Right>', on_right)
                entry.bind('<Up>', on_up)
                entry.bind('<Down>', on_down)
            
            edit_entry_by_col(item, col)
    
    tree.bind('<Double-1>', on_double_click)
    # 初始合计
    calc_total()
    
    # 备注区域
    remark_frame = ttk.Frame(dialog)
    remark_frame.pack(fill=tk.X, padx=30, pady=8)
    ttk.Label(remark_frame, text="订单备注:", font=('微软雅黑', 11)).pack(side=tk.LEFT)
    remark_var = tk.StringVar(value="")
    remark_entry = ttk.Entry(remark_frame, textvariable=remark_var, width=50)
    remark_entry.pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)

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
            product_id = vals[7]  # product_id
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
        
        # 3. 生成订单号
        if not order_no_var.get():
            today_str = now.strftime('%Y%m%d')
            all_orders = dbutil.get_all_outbound_orders()
            today_orders = [o for o in all_orders if o[1].startswith(f"QH{today_str}")]
            order_seq = len(today_orders) + 1
            order_no = f"QH{today_str}{order_seq:04d}"
            order_no_var.set(order_no)
            order_no_entry.update()
        
        # 4. 生成出库单（写入数据库）
        try:

            total = float(total_var.get())
            now_str = now.strftime('%Y-%m-%d %H:%M:%S')
            
            # 获取客户id
            customer_id = None
            for c in customers:
                if c[1] == customer_var.get():
                    customer_id = c[0]
                    break
            
            # 确定支付状态
            pay_status = 0 if float(total_paid_var.get()) == 0 else 1 if float(total_paid_var.get()) < total else 2
            
            # 获取备注内容
            remark = remark_var.get()
            outbound_id = dbutil.insert_outbound_order(
                order_no_var.get(), customer_id, total, pay_status, float(total_paid_var.get()), float(total_debt_var.get()), now_str, remark
            )
            
            # 初始化item_ids列表
            item_ids = []
            
            for idx, item in enumerate(tree.get_children()):
                vals = tree.item(item)['values']
                product_id = vals[7]  # product_id
                quantity = int(vals[4]) if vals[4] else 0
                price = float(vals[5]) if vals[5] else 0
                amount = float(vals[6]) if vals[6] else 0
                size = vals[3]  # 重新获取size变量
                
                item_id = dbutil.insert_outbound_item(
                    outbound_id, product_id, quantity, price, amount
                )
                dbutil.update_inventory_size_by_id(product_id, size)
                dbutil.decrease_inventory_by_id(product_id, quantity)
                item_ids.append(str(item_id))
        
            # 6. 收集所有item_ids
            item_ids_str = ','.join(item_ids)
            
            # 7. 如果余款金额不为0，写入debt_record表
            remaining_debt = float(total_debt_var.get())
            if remaining_debt > 0:
                 dbutil.insert_debt_record(outbound_id, item_ids_str, remaining_debt)
                  
            # 8. 如果有支付金额，写入payment_record表
            payment_amount = float(total_paid_var.get())
            if payment_amount > 0:
                 pay_method = pay_method_var.get()
                 dbutil.insert_payment_record(outbound_id, item_ids_str, payment_amount, now_str, pay_method)

        except Exception as e:
            messagebox.showerror("错误", f"保存出库单失败：{e}")
            return
        
        # 5. 提示是否输出为PDF
        if messagebox.askyesno("出库单已保存", "是否输出为PDF？"):
            try:
                from pages.dialog.outbound_detail_dialog import show_outbound_detail
                show_outbound_detail(None, order_no)
            except Exception as e:
                messagebox.showerror("错误", f"打开出库单详情失败：{e}")
        
        # 自动删除暂存单（如有）
        if cart_list and customer_name:
            all_drafts = dbutil.get_all_draft_orders()
            match_id = None
            for d in all_drafts:
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
            
            # 获取备注内容
            remark = remark_var.get()
            draft_id = dbutil.insert_draft_order(customer_id, total, remark, now_str)
            
            for item in tree.get_children():
                vals = tree.item(item)['values']
                product_id = vals[7]  # product_id
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
