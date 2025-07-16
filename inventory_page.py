import tkinter as tk
from tkinter import ttk
from util import dbutil

def InventoryPage(parent):
    frame = ttk.Frame(parent)
    # 供出库单页面调用，刷新库存和清空待出库数量
    def refresh():
        load_data()
        cart_list.clear()
        cart_count.set(0)
        update_cart_btn()
    frame.refresh = refresh
    # 搜索栏
    search_frame = ttk.Frame(frame)
    search_frame.pack(fill=tk.X, padx=10, pady=8)
    ttk.Label(search_frame, text="厂家:").pack(side=tk.LEFT)
    search_factory = tk.StringVar()
    ttk.Entry(search_frame, textvariable=search_factory, width=12).pack(side=tk.LEFT, padx=4)
    ttk.Label(search_frame, text="货号:").pack(side=tk.LEFT)
    search_product_no = tk.StringVar()
    ttk.Entry(search_frame, textvariable=search_product_no, width=12).pack(side=tk.LEFT, padx=4)
    # 右侧待出库按钮
    cart_count = tk.IntVar(value=0)
    cart_btn_var = tk.StringVar()
    def update_cart_btn():
        cart_btn_var.set(f"待出库{cart_count.get()}")
    def show_cart():
        if not cart_list:
            tk.messagebox.showinfo("待出库", "当前待出库为空！")
            return
        # 弹出出库单页面
        try:
            from outbound_dialog import OutboundDialog
        except ImportError:
            tk.messagebox.showerror("错误", "未找到出库单页面模块！")
            return
        OutboundDialog(frame, cart_list)
    cart_btn = tk.Button(search_frame, textvariable=cart_btn_var, width=12, command=show_cart,
                        bg="#b7f7b0", activebackground="#a0e89c", fg="#1a3d1a", relief=tk.RAISED, bd=2, font=("微软雅黑", 10, "bold"))
    cart_btn.pack(side=tk.RIGHT, padx=10)
    update_cart_btn()
    # 表格区
    columns = ("no", "factory", "product_no", "color", "quantity")
    headers = [
        ("no", "序号"),
        ("factory", "厂家"),
        ("product_no", "货号"),
        ("color", "颜色"),
        ("quantity", "库存数量")
    ]
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=90)
    # 待出库数据结构
    cart_list = []  # [(row, 出库数量, 单价)]
    def load_data():
        for row in tree.get_children():
            tree.delete(row)
        all_rows = dbutil.get_all_inventory()
        # 搜索过滤
        factory = search_factory.get().strip()
        product_no = search_product_no.get().strip()
        filtered = []
        for r in all_rows:
            # r: (id, stock_id, factory, product_no, color, quantity)
            if factory and factory not in (r[2] or ""):
                continue
            if product_no and product_no not in (r[3] or ""):
                continue
            filtered.append(r)
        for idx, row in enumerate(filtered, 1):
            # 隐藏id/stock_id，首列为序号
            # row: (id, stock_id, factory, product_no, color, quantity)
            values = [idx, row[2], row[3], row[4], row[5]]
            tree.insert("", tk.END, values=values, tags=(str(row[0]),))
    def do_search():
        load_data()
    ttk.Button(search_frame, text="搜索", command=do_search, width=8).pack(side=tk.LEFT, padx=8)
    # 右键菜单
    menu = tk.Menu(tree, tearoff=0)
    def on_outbound():
        selected = tree.selection()
        if not selected:
            tk.messagebox.showwarning("提示", "请先选择要出库的库存记录！")
            return
        item = tree.item(selected[0])
        values = item['values']
        # 弹窗输入出库数量及单价
        dialog = tk.Toplevel(frame)
        dialog.title("出库信息")
        dialog.transient(frame)
        dialog.grab_set()
        dialog.update_idletasks()
        w, h = 340, 230
        x = dialog.winfo_screenwidth() // 2 - w // 2
        y = dialog.winfo_screenheight() // 2 - h // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        tk.Label(dialog, text=f"出库【{values[1]} {values[2]} {values[3]} {values[4]}】", font=("微软雅黑", 11)).pack(pady=(18, 8))
        entry_frame = ttk.Frame(dialog)
        entry_frame.pack(pady=2)
        qty_var = tk.StringVar()
        price_var = tk.StringVar()
        ttk.Label(entry_frame, text="出库数量:").grid(row=0, column=0, padx=4, pady=6)
        qty_entry = ttk.Entry(entry_frame, textvariable=qty_var, width=10, justify='center')
        qty_entry.grid(row=0, column=1, padx=4)
        ttk.Label(entry_frame, text="单价:").grid(row=1, column=0, padx=4, pady=6)
        price_entry = ttk.Entry(entry_frame, textvariable=price_var, width=10, justify='center')
        price_entry.grid(row=1, column=1, padx=4)
        error_label = tk.Label(dialog, text="", fg="red")
        error_label.pack(pady=2)
        def confirm():
            try:
                qty = int(qty_var.get())
                if qty <= 0 or qty > int(values[4]):
                    error_label['text'] = "数量需大于0且不超过库存！"
                    return
                price = float(price_var.get())
                if price < 0:
                    error_label['text'] = "单价不能为负数！"
                    return
            except Exception:
                error_label['text'] = "请输入有效数字！"
                return
            # 加入待出库，附带单价
            # values: [序号, factory, product_no, color, quantity]，需带上id
            # 通过 tags 获取库存id
            inventory_id = None
            if selected:
                tags = tree.item(selected[0]).get('tags', [])
                if tags:
                    inventory_id = int(tags[0])
            # 构造带id的values，便于后续出库单处理
            values_with_id = [inventory_id] + list(values)
            cart_list.append((values_with_id, qty, price))
            cart_count.set(cart_count.get() + 1)
            update_cart_btn()
            dialog.destroy()
        ttk.Button(dialog, text="确定", command=confirm, width=10).pack(pady=10)
        qty_entry.focus_set()
        dialog.wait_window()
    menu.add_command(label="出库", command=on_outbound)
    def show_menu(event):
        row_id = tree.identify_row(event.y)
        if row_id:
            tree.selection_set(row_id)
            menu.tk_popup(event.x_root, event.y_root)
    tree.bind("<Button-3>", show_menu)
    load_data()
    return frame
