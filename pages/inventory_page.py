# 库存管理页面
import tkinter as tk
from tkinter import ttk
from util import dbutil
from tkinter import messagebox, filedialog
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def InventoryPage(parent):

    frame = ttk.Frame(parent)
    # 供出库单页面调用，仅刷新库存
    def refresh():
        load_data()
        cart_list.clear()
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
    # "制作出库单"按钮，弹出空白出库单
    def show_make_outbound():
        try:
            from pages.dialog.outbound_dialog import OutboundDialog
        except ImportError:
            tk.messagebox.showerror("错误", "未找到出库单页面模块！")
            return
        OutboundDialog(frame, [])  # 传空列表，弹出空白出库单

    def show_draft_list():
        try:
            from pages.dialog.outbound_dialog import OutboundDialog
        except ImportError:
            tk.messagebox.showerror("错误", "未找到出库单页面模块！")
            return
        # 查询所有暂存出库单（从 draft_order 表获取）
        drafts = dbutil.get_all_draft_orders()  # [(id, customer_id, total, remark, create_time)]
        win = tk.Toplevel(frame)
        win.title("暂存出库单列表")
        win.geometry("900x400")
        columns = ("draft_id", "customer", "total", "create_time")
        tree = ttk.Treeview(win, columns=columns, show="headings", height=12)
        tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        tree.heading("draft_id", text="暂存单ID")
        tree.heading("customer", text="客户")
        tree.heading("total", text="金额")
        tree.heading("create_time", text="创建时间")
        customer_names = []
        for o in drafts:
            customer_name = ''
            try:
                customer = dbutil.get_customer_by_id(o[1])
                customer_name = customer[1] if customer else ''
            except Exception:
                pass
            customer_names.append(customer_name)
            tree.insert('', tk.END, values=(o[0], customer_name, f"{o[2]:.2f}", o[4]))
        def on_double_click(event):
            sel = tree.selection()
            if not sel:
                return
            idx = tree.index(sel[0])
            draft = drafts[idx]
            customer_name = customer_names[idx]
            # 获取明细（从 draft_item 表获取）
            items = dbutil.get_draft_items_by_order(draft[0])
            # 将draft_id添加到cart_list中，以便在outbound_dialog中可以正确删除暂存单
            cart_list = {'draft_id': draft[0], 'items': []}
            for item in items:
                inv = dbutil.get_inventory_by_id(item[2])
                cart_list['items'].append((inv, item[3], item[4]))
            win.destroy()
            # 进入出库单时自动带出客户姓名
            # 直接传递客户姓名和draft_id给弹窗
            OutboundDialog(frame, cart_list, customer_name)
        tree.bind('<Double-1>', on_double_click)

        # 鼠标悬停时显示“双击编辑”提示
        def on_motion(event):
            tree_tooltip = getattr(tree, '_tooltip', None)
            region = tree.identify('region', event.x, event.y)
            if region == 'cell':
                if not tree_tooltip:
                    tree._tooltip = tk.Label(win, text="双击编辑", bg="#ffffe0", fg="#333", font=("微软雅黑", 10), relief=tk.SOLID, bd=1)
                tooltip = tree._tooltip
                tooltip.place(x=event.x_root - win.winfo_rootx() + 10, y=event.y_root - win.winfo_rooty() + 10)
            else:
                if tree_tooltip:
                    tree_tooltip.place_forget()
        tree.bind('<Motion>', on_motion)

        def delete_selected_draft():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("提示", "请先选择要删除的暂存单！")
                return
            idx = tree.index(sel[0])
            draft = drafts[idx]
            draft_id = draft[0]
            dbutil.delete_draft_order(draft_id)
            tree.delete(sel[0])
            messagebox.showinfo("删除成功", "暂存单已删除！")

        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="删除选中暂存单", command=delete_selected_draft).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="关闭", command=win.destroy).pack(side=tk.LEFT, padx=8)

    draft_btn = tk.Button(search_frame, text="暂存单", width=10, command=show_draft_list,
                        bg="#e6e6e6", activebackground="#cccccc", fg="#333333", relief=tk.RAISED, bd=2, font=("微软雅黑", 10))
    draft_btn.pack(side=tk.RIGHT, padx=4)
    make_btn = tk.Button(search_frame, text="制作出库单", width=14, command=show_make_outbound,
                        bg="#b7f7b0", activebackground="#a0e89c", fg="#1a3d1a", relief=tk.RAISED, bd=2, font=("微软雅黑", 10, "bold"))
    make_btn.pack(side=tk.RIGHT, padx=10)
    # 表格区
    columns = ("no", "factory", "product_no", "size", "color","unit", "quantity")
    headers = [
        ("no", "序号"),
        ("factory", "厂家"),
        ("product_no", "货号"),
        ("size", "尺码"),
        ("color", "颜色"),
        ("unit", "单位"),
        ("quantity", "库存数量")
    ]
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
    # 添加垂直滚动条
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=10)
    vsb.pack(side=tk.LEFT, fill=tk.Y, pady=10)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=90)
    # 待出库数据结构（仅保留，实际已不用）
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
            values = [idx, row[2], row[3], row[4], row[5], row[6], row[7]]
            tree.insert("", tk.END, values=values, tags=(str(row[0]),))
    def do_search():
        load_data()
    ttk.Button(search_frame, text="搜索", command=do_search, width=8).pack(side=tk.LEFT, padx=8)
    # 绑定回车键事件
    search_factory_entry = search_frame.winfo_children()[2]  # 获取厂家输入框
    search_product_entry = search_frame.winfo_children()[4]  # 获取货号输入框
    search_factory_entry.bind('<Return>', lambda e: do_search())
    search_product_entry.bind('<Return>', lambda e: do_search())
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
        headers = ["序号", "厂家", "货号", "尺码", "颜色","单位", "库存数量"]
        c.setFont(font_normal, 11)
        y = height - 80
        col_widths = [40, 80, 80, 60, 60,40, 80]
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
            values = [str(idx), row[2], row[3], row[4], row[5], str(row[6]),str(row[7])]
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
