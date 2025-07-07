#库存页面
import tkinter as tk
from tkinter import ttk
from util.utils import center_window
from util import dbutil
import util.utils as utils

def StockPage(parent, main_win):
    frame = ttk.Frame(parent)
    # 工具栏（包含按钮和搜索控件）
    stock_toolbar = ttk.Frame(frame)
    stock_toolbar.pack(fill=tk.X, padx=10, pady=10, anchor=tk.N)
    # 左侧按钮
    btn_add = ttk.Button(stock_toolbar, text="➕", width=3)
    btn_add.pack(side=tk.LEFT, padx=3)
    def add_tooltip(widget, text):
        tip = tk.Toplevel(widget)
        tip.withdraw()
        tip.overrideredirect(True)
        label = tk.Label(tip, text=text, background="#ffffe0", relief=tk.SOLID, borderwidth=1, font=("微软雅黑", 9))
        label.pack(ipadx=4)
        def enter(event):
            x, y, cx, cy = widget.bbox("insert") if hasattr(widget, 'bbox') else (0, 0, 0, 0)
            x += widget.winfo_rootx() + 30
            y += widget.winfo_rooty() + 20
            tip.geometry(f"+{x}+{y}")
            tip.deiconify()
        def leave(event):
            tip.withdraw()
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
    add_tooltip(btn_add, "新增库存")
    btn_del = ttk.Button(stock_toolbar, text="🗑️", width=3)
    btn_del.pack(side=tk.LEFT, padx=3)
    add_tooltip(btn_del, "删除/返厂")
    btn_edit = ttk.Button(stock_toolbar, text="✏️", width=3)
    btn_edit.pack(side=tk.LEFT, padx=3)
    add_tooltip(btn_edit, "修改库存")
    # 右侧搜索控件
    search_frame = ttk.Frame(stock_toolbar)
    search_frame.pack(side=tk.RIGHT, padx=0)
    ttk.Label(search_frame, text="厂家:").pack(side=tk.LEFT)
    search_factory = tk.StringVar()
    ttk.Entry(search_frame, textvariable=search_factory, width=10).pack(side=tk.LEFT, padx=3)
    ttk.Label(search_frame, text="货号:").pack(side=tk.LEFT)
    search_product_no = tk.StringVar()
    ttk.Entry(search_frame, textvariable=search_product_no, width=10).pack(side=tk.LEFT, padx=3)
    ttk.Label(search_frame, text="是否结账:").pack(side=tk.LEFT)
    search_settled = tk.StringVar(value="全部")
    ttk.Combobox(search_frame, textvariable=search_settled, values=["全部", "是", "否"], width=5, state="readonly").pack(side=tk.LEFT, padx=3)
    def do_search():
        factory = search_factory.get().strip()
        product_no = search_product_no.get().strip()
        settled = search_settled.get()
        results = []
        for row in dbutil.get_all_stock():
            _, f, p, _, _, _, _, _, s = row
            if factory and factory not in f:
                continue
            if product_no and product_no not in p:
                continue
            if settled != "全部":
                if (settled == "是" and not s) or (settled == "否" and s):
                    continue
            results.append(row)
        # 刷新表格
        for r in tree.get_children():
            tree.delete(r)
        for idx, row in enumerate(results, 1):
            id_, factory, product_no, size, color, in_quantity, price, total, is_settled = row
            is_settled = "是" if is_settled else "否"
            tree.insert("", tk.END, iid=str(id_), values=[
                idx, 
                factory, 
                product_no, 
                size, 
                color, 
                in_quantity,  # 入库数量
                price,  # 单价
                total, 
                is_settled
            ])
    ttk.Button(search_frame, text="搜索", command=do_search, width=8).pack(side=tk.LEFT, padx=6)
    # 表格区，隐藏id，新增序号列，去掉可用数量
    columns = ("no", "factory", "product_no", "size", "color", "in_quantity", "price", "total", "is_settled")
    headers = [
        ("no", "序号"),
        ("factory", "厂家"),
        ("product_no", "货号"),
        ("size", "尺码"),
        ("color", "颜色"),
        ("in_quantity", "入库数量"),
        ("price", "单价"),
        ("total", "合计"),
        ("is_settled", "是否结账")
    ]
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=12, selectmode="extended")
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    # 右键菜单
    menu = tk.Menu(tree, tearoff=0)
    def on_settle_selected():
        selected = tree.selection()
        if not selected:
            tk.messagebox.showwarning("提示", "请先选择要结账的库存记录！")
            return
        # 创建日期选择对话框
        date_dialog = tk.Toplevel(main_win)
        date_dialog.title("选择结账日期")
        date_dialog.transient(main_win)
        date_dialog.grab_set()
        center_window(date_dialog, 300, 120)
        ttk.Label(date_dialog, text="请选择结账日期:").pack(pady=10)
        date_var = tk.StringVar()
        date_entry = ttk.Entry(date_dialog, textvariable=date_var)
        date_entry.pack(pady=5)
        date_entry.insert(0, utils.get_current_date())  # 默认当前日期
        def confirm_settle():
            settle_date = date_var.get()
            if not settle_date:
                tk.messagebox.showwarning("提示", "请选择结账日期！")
                return
            # 检测已结账物品
            settled_items = []
            for iid in selected:
                item = tree.item(iid)
                values = item['values']
                if values[9] == "是":  # 如果第10列(是否结账)为"是"
                    settled_items.append(values)
            if settled_items:
                message = "以下物品已结账，确定要重复结账吗？\n\n"
                for item in settled_items:
                    message += f"厂家: {item[1]} 货号: {item[2]} 颜色: {item[4]} 尺码: {item[3]}\n"
                if not tk.messagebox.askyesno("警告", message):
                    date_dialog.destroy()
                    return
            for iid in selected:
                dbutil.settle_stock_by_id(iid)
                # 写入结账日志
                item = tree.item(iid)
                values = item['values']
                dbutil.insert_settle_log(
                    values[1],  # factory
                    values[2],  # product_no
                    values[3],  # size
                    values[4],  # color
                    int(values[5]),  # in_quantity
                    float(values[6]),  # price
                    float(values[7]),  # total
                    settle_date
                )
            # 自动刷新日志页面
            if hasattr(main_win, 'refresh_logs'):
                main_win.refresh_logs()
            load_stock_data()
            date_dialog.destroy()
            tk.messagebox.showinfo("结账", f"所选记录已结账！\n结账日期: {settle_date}")
        ttk.Button(date_dialog, text="确定", command=confirm_settle).pack(pady=10)
    menu.add_command(label="结账", command=on_settle_selected)
    def show_menu(event):
        row_id = tree.identify_row(event.y)
        if row_id:
            # 如果右键行不在当前多选中，才切换 selection
            if row_id not in tree.selection():
                tree.selection_set(row_id)
            menu.tk_popup(event.x_root, event.y_root)
    tree.bind("<Button-3>", show_menu)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=80)
    def load_stock_data():
        for row in tree.get_children():
            tree.delete(row)
        for idx, row in enumerate(dbutil.get_all_stock(), 1):
            id_, factory, product_no, size, color, in_quantity, price, total, is_settled = row
            is_settled = "是" if is_settled else "否"
            tree.insert("", tk.END, iid=str(id_), values=[idx, factory, product_no, size, color, in_quantity, price, total, is_settled])
    load_stock_data()
    # 新增库存后刷新表格
    def open_add_stock_dialog_and_refresh():
        open_add_stock_dialog()
        load_stock_data()
    # 替换按钮绑定
    btn_add.config(command=open_add_stock_dialog_and_refresh)
    def on_delete_or_return():
        selected = tree.selection()
        if not selected:
            tk.messagebox.showwarning("提示", "请先选择要操作的库存记录！")
            return
        item = tree.item(selected[0])
        values = item['values']
        factory, product_no, size, color = values[1], values[2], values[3], values[4]
        # 自定义操作对话框
        dialog = tk.Toplevel(main_win)
        dialog.title("请选择操作")
        dialog.transient(main_win)
        dialog.grab_set()
        center_window(dialog, 260, 120)
        msg = f"对【{factory} {product_no} {color} {size}】请选择操作："
        ttk.Label(dialog, text=msg, wraplength=240, font=("微软雅黑", 10)).pack(pady=(18, 10))
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=5)
        def do_return():
            dialog.destroy()
            # 写入返厂日志
            dbutil.insert_stock_log(
                factory, product_no, size, color, int(values[5]), '返厂', utils.get_current_date()
            )
            # 自动刷新日志页面
            if hasattr(main_win, 'refresh_logs'):
                main_win.refresh_logs()
            tk.messagebox.showinfo("返厂", f"已将【{factory} {product_no} {color} {size}】标记为返厂！")
        def do_delete():
            dialog.destroy()
            stock_id = tree.selection()[0]
            dbutil.delete_stock_by_id(stock_id)
            load_stock_data()
            tk.messagebox.showinfo("删除", "删除成功！")
        def do_cancel():
            dialog.destroy()
        ttk.Button(btn_frame, text="返厂", width=8, command=do_return).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="删除", width=8, command=do_delete).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="取消", width=8, command=do_cancel).pack(side=tk.LEFT, padx=8)
        dialog.wait_window()
    # 修改工具栏按钮
    for widget in stock_toolbar.winfo_children():
        if isinstance(widget, ttk.Button) and widget["text"] == "删除/返厂":
            widget.config(text="删除/返厂", command=on_delete_or_return)
    def open_edit_stock_dialog():
        selected = tree.selection()
        if not selected:
            tk.messagebox.showwarning("提示", "请先选择要修改的库存记录！")
            return
        item = tree.item(selected[0])
        values = item['values']
        stock_id = selected[0]
        dialog = tk.Toplevel(main_win)
        dialog.title("修改入库")
        dialog.transient(main_win)
        dialog.grab_set()
        center_window(dialog, 380, 230)
        fields = [
            ("厂家", "factory"),
            ("货号", "product_no"),
            ("尺码", "size"),
            ("颜色", "color"),
            ("入库数量", "in_quantity"),
            ("单价", "price"),
            ("合计", "total")
        ]
        vars = {}
        entry_refs = {}
        vars = {}
        for idx, (label, key) in enumerate(fields):
            vars[key] = tk.StringVar()
            if key in ["in_quantity", "price"]:
                vars[key].trace_add("write", lambda *args: vars["total"].set(utils.calculate_total(vars["in_quantity"].get(), vars["price"].get())))
        entry_refs = {}
        for idx, (label, key) in enumerate(fields[:-1]):
            row = idx // 2
            col = (idx % 2) * 2
            ttk.Label(dialog, text=label+":").grid(row=row, column=col, sticky=tk.W, padx=10, pady=8)
            var = tk.StringVar()
            if key == 'price':
                def validate_price(new_value):
                    if new_value == "":
                        return True
                    if new_value.count('.') > 1:
                        return False
                    if new_value.startswith('.'):
                        return False
                    return all(c.isdigit() or c == '.' for c in new_value)
                vcmd = dialog.register(validate_price)
                entry = ttk.Entry(dialog, textvariable=var, validate="key", validatecommand=(vcmd, '%P'))
            else:
                entry = ttk.Entry(dialog, textvariable=var)
            entry.configure(width=15)
            entry.grid(row=row, column=col+1, sticky=tk.W+tk.E, padx=5)
            vars[key] = var
            entry_refs[key] = entry
        ttk.Label(dialog, text="合计:").grid(row=4, column=2, sticky=tk.E, padx=10, pady=8)
        total_var = tk.StringVar()
        total_entry = ttk.Entry(dialog, textvariable=total_var, state='readonly', justify='right')
        total_entry.configure(width=15)
        total_entry.grid(row=4, column=3, sticky=tk.W+tk.E, padx=5)
        vars['total'] = total_var
        keys = ["factory", "product_no", "size", "color", "in_quantity", "price", "total"]
        for i, k in enumerate(keys):
            vars[k].set(values[i+1])
        def update_total(*args):
            vars['total'].set(utils.calculate_total(vars['in_quantity'].get(), vars['price'].get()))
        vars['in_quantity'].trace_add('write', update_total)
        vars['price'].trace_add('write', update_total)
        def on_ok():
            for k, v in vars.items():
                if k != 'total' and not v.get().strip():
                    error_label['text'] = "所有字段不能为空！"
                    return
            try:
                dbutil.update_stock_by_id(
                    stock_id,
                    vars['factory'].get().strip(),
                    vars['product_no'].get().strip(),
                    vars['size'].get().strip(),
                    vars['color'].get().strip(),
                    int(vars['in_quantity'].get()),
                    float(vars['price'].get()),
                    float(vars['total'].get())
                )
                tk.messagebox.showinfo("成功", "修改成功！")
                dialog.destroy()
                load_stock_data()
            except Exception as e:
                error_label['text'] = str(e)
        ttk.Button(dialog, text="确定修改", command=on_ok, width=12).grid(row=5, column=0, columnspan=4, pady=10)
        error_label = tk.Label(dialog, text="", fg="red", font=("微软雅黑", 10))
        error_label.grid(row=6, column=0, columnspan=4, pady=(0, 5))
        dialog.after(100, lambda: entry_refs['factory'].focus_set())
        dialog.wait_window()
    # 修改按钮绑定
    for widget in stock_toolbar.winfo_children():
        if isinstance(widget, ttk.Button) and widget["text"] == "修改库存":
            widget.config(command=open_edit_stock_dialog)
    # 绑定按钮功能（确保图标按钮功能正常）
    btn_del.config(command=on_delete_or_return)
    btn_edit.config(command=open_edit_stock_dialog)
    def open_add_stock_dialog():
        dialog = tk.Toplevel(main_win)
        dialog.title("新增库存")
        dialog.transient(main_win)
        dialog.grab_set()
        center_window(dialog, 450, 230)
        fields = [
            ("厂家", "factory"),
            ("货号", "product_no"),
            ("尺码", "size"),
            ("颜色", "color"),
            ("入库数量", "in_quantity"),
            ("单价", "price"),
            ("合计", "total")
        ]
        vars = {}
        entry_refs = {}
        # 初始化变量
        vars = {}
        for idx, (label, key) in enumerate(fields):
            vars[key] = tk.StringVar()
        # 创建输入框并绑定计算事件
        entry_refs = {}
        for idx, (label, key) in enumerate(fields[:-1]):
            row = idx // 2
            col = (idx % 2) * 2
            ttk.Label(dialog, text=label+":").grid(row=row, column=col, sticky=tk.W, padx=10, pady=8)
            var = tk.StringVar()
            if key in ['in_quantity', 'price']:
                var.trace_add('write', lambda *args: update_total(vars))
            if key == 'price':
                def validate_price(new_value):
                    if new_value == "":
                        return True
                    if new_value.count('.') > 1:
                        return False
                    if new_value.startswith('.'):
                        return False
                    return all(c.isdigit() or c == '.' for c in new_value)
                vcmd = dialog.register(validate_price)
                entry = ttk.Entry(dialog, textvariable=var, validate="key", validatecommand=(vcmd, '%P'))
            else:
                entry = ttk.Entry(dialog, textvariable=var)
            entry.grid(row=row, column=col+1, sticky=tk.W+tk.E, padx=5)
            vars[key] = var
            entry_refs[key] = entry
        def update_total(vars):
            vars["total"].set(utils.calculate_total(vars["in_quantity"].get(), vars["price"].get()))
        ttk.Label(dialog, text="合计:").grid(row=4, column=2, sticky=tk.E, padx=10, pady=8)
        total_var = tk.StringVar()
        total_entry = ttk.Entry(dialog, textvariable=total_var, state='readonly', justify='right')
        total_entry.grid(row=4, column=3, sticky=tk.W+tk.E, padx=5)
        vars['total'] = total_var
        def on_add():
            for k, v in vars.items():
                if k != 'total' and not v.get().strip():
                    error_label['text'] = "所有字段不能为空！"
                    return
            try:
                vars["total"].set(utils.calculate_total(vars["in_quantity"].get(), vars["price"].get()))
                dbutil.insert_stock(
                    vars['factory'].get().strip(),
                    vars['product_no'].get().strip(),
                    vars['size'].get().strip(),
                    vars['color'].get().strip(),
                    int(vars['in_quantity'].get()),
                    float(vars['price'].get()),
                    float(vars['total'].get())
                )
                # 获取最新入库id
                stock_rows = dbutil.get_all_stock()
                if stock_rows:
                    stock_id = stock_rows[0][0]  # 最新一条id
                    dbutil.insert_inventory_from_stock(
                        stock_id,
                        vars['factory'].get().strip(),
                        vars['product_no'].get().strip(),
                        vars['size'].get().strip(),
                        vars['color'].get().strip(),
                        int(vars['in_quantity'].get())
                    )
                # 写入入库日志
                dbutil.insert_stock_log(
                    vars['factory'].get().strip(),
                    vars['product_no'].get().strip(),
                    vars['size'].get().strip(),
                    vars['color'].get().strip(),
                    int(vars['in_quantity'].get()),
                    '入库',
                    utils.get_current_date()
                )
                # 自动刷新日志页面
                if hasattr(main_win, 'refresh_logs'):
                    main_win.refresh_logs()
                tk.messagebox.showinfo("成功", "新增成功！")
                dialog.destroy()
                load_stock_data()
            except Exception as e:
                error_label['text'] = str(e)
        ttk.Button(dialog, text="确定新增", command=on_add, width=12).grid(row=5, column=0, columnspan=4, pady=10)
        error_label = tk.Label(dialog, text="", fg="red", font=("微软雅黑", 10))
        error_label.grid(row=6, column=0, columnspan=4, pady=(0, 5))
        dialog.after(100, lambda: entry_refs['factory'].focus_set())
        dialog.wait_window()
    return frame