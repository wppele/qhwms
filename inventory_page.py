import tkinter as tk
from tkinter import ttk
from util import dbutil
from tkinter import messagebox, filedialog
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def InventoryPage(parent):
    # 鼠标悬停表格项时显示提示
    def show_tooltip(event):
        widget = event.widget
        row_id = widget.identify_row(event.y)
        if row_id:
            if not hasattr(widget, '_tooltip_label'):
                widget._tooltip_label = tk.Label(widget, text="双击出库", bg="#ffffe0", fg="#333", font=("微软雅黑", 10), relief=tk.SOLID, bd=1)
            widget._tooltip_label.place_forget()
            widget._tooltip_label.place(x=event.x, y=event.y+18)
        else:
            if hasattr(widget, '_tooltip_label'):
                widget._tooltip_label.place_forget()

    def hide_tooltip(event):
        widget = event.widget
        if hasattr(widget, '_tooltip_label'):
            widget._tooltip_label.place_forget()

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
    columns = ("no", "factory", "product_no", "size", "color", "quantity")
    headers = [
        ("no", "序号"),
        ("factory", "厂家"),
        ("product_no", "货号"),
        ("size", "尺码"),
        ("color", "颜色"),
        ("quantity", "库存数量")
    ]
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=90)

    tree.bind('<Motion>', show_tooltip)
    tree.bind('<Leave>', hide_tooltip)
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
            # r: (id, stock_id, factory, product_no, size, color, quantity)
            if factory and factory not in (r[2] or ""):
                continue
            if product_no and product_no not in (r[3] or ""):
                continue
            filtered.append(r)
        for idx, row in enumerate(filtered, 1):
            # 隐藏id/stock_id，首列为序号
            values = [idx, row[2], row[3], row[4], row[5], row[6]]
            tree.insert("", tk.END, values=values, tags=(str(row[0]),))
    def do_search():
        load_data()
    ttk.Button(search_frame, text="搜索", command=do_search, width=8).pack(side=tk.LEFT, padx=8)
    # 双击出库
    def on_outbound(event):
        row_id = tree.identify_row(event.y)
        if not row_id:
            return
        tree.selection_set(row_id)
        selected = tree.selection()
        if not selected:
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
                if qty <= 0 or qty > int(values[5]):
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
            inventory_id = None
            tags = tree.item(selected[0]).get('tags', [])
            if tags:
                inventory_id = int(tags[0])
            values_with_id = [inventory_id] + list(values)
            cart_list.append((values_with_id, qty, price))
            cart_count.set(cart_count.get() + 1)
            update_cart_btn()
            dialog.destroy()
        ttk.Button(dialog, text="确定", command=confirm, width=10).pack(pady=10)
        qty_entry.focus_set()
        dialog.wait_window()
    tree.bind("<Double-1>", on_outbound)
    load_data()

    def export_inventory():
        all_rows = dbutil.get_all_inventory()
        factory = search_factory.get().strip()
        product_no = search_product_no.get().strip()
        filtered = []
        for r in all_rows:
            if factory and factory not in (r[2] or ""):
                continue
            if product_no and product_no not in (r[3] or ""):
                continue
            filtered.append(r)
        if not filtered:
            messagebox.showinfo("导出库存", "没有可导出的库存数据！")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF文件", "*.pdf")], title="导出库存")
        if not file_path:
            return
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from util import utils
        font_title, font_normal = utils.set_pdf_chinese_font(pdfmetrics, TTFont)
        title = "库存列表"
        c.setFont(font_title, 16)
        # 标题居中
        c.drawCentredString(width // 2, height - 50, title)
        headers = ["序号", "厂家", "货号", "尺码", "颜色", "库存数量"]
        c.setFont(font_normal, 11)
        y = height - 80
        col_widths = [40, 80, 80, 60, 60, 80]
        # 表头（带线）
        x = 60
        from reportlab.lib.colors import HexColor
        line_height = 20
        c.setFont(font_normal, 11)
        for i, h in enumerate(headers):
            c.setStrokeColor(HexColor('#888888'))
            c.rect(x, y, col_widths[i], line_height, stroke=1, fill=0)
            c.setFillColor(HexColor('#000000'))
            # 表头内容居中
            c.drawCentredString(x + col_widths[i] // 2, y + line_height // 2, h)
            x += col_widths[i]
        y -= line_height
        # 数据（带线）
        for idx, row in enumerate(filtered, 1):
            x = 60
            values = [str(idx), row[2], row[3], row[4], row[5], str(row[6])]
            for i, v in enumerate(values):
                c.setStrokeColor(HexColor('#aaaaaa'))
                c.rect(x, y, col_widths[i], line_height, stroke=1, fill=0)
                c.setFillColor(HexColor('#000000'))
                # 数据内容居中
                c.drawCentredString(x + col_widths[i] // 2, y + line_height // 2, v)
                x += col_widths[i]
            y -= line_height
            if y < 60:
                c.showPage()
                c.setFont(font_normal, 11)
                y = height - 60
        c.save()
        messagebox.showinfo("导出成功", f"库存已导出到：{file_path}")
    ttk.Button(search_frame, text="导出库存", command=export_inventory, width=10).pack(side=tk.LEFT, padx=4)
    return frame
