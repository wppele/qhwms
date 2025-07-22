import tkinter as tk
from tkinter import ttk
from util import dbutil
import tkinter.simpledialog
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
    columns = ("idx", "product_no", "color", "size", "quantity", "price", "amount", "item_pay_status", "debt_amount")
    headers = [
        ("idx", "序号"),
        ("product_no", "货号"),
        ("color", "颜色"),
        ("size", "尺码"),
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
        size = inv[3] if inv else ''
        quantity = item[3]
        price = item[4] if len(item) > 4 else 0.0
        amount = item[5] if len(item) > 5 else 0.0
        total_amount += amount
        paid = item[7] if len(item) > 7 else 0
        total_paid += paid
        debt = item[8] if len(item) > 8 else 0
        total_debt += debt
        tree.insert('', tk.END, values=(
            idx, product_no, color, size, quantity, f"{price:.2f}", f"{amount:.2f}",
            "已付" if item[6]==1 else "欠款", f"{debt:.2f}"
        ))
    # 右下角统计和按钮
    bottom = ttk.Frame(win)
    bottom.pack(fill=tk.X, side=tk.BOTTOM, anchor=tk.SE, padx=24, pady=12)
    is_kufang = tk.BooleanVar(value=True)
    def do_export():
        from tkinter import filedialog
        from reportlab.pdfgen import canvas as pdfcanvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from util import utils
        font_title, font_normal = utils.set_pdf_chinese_font(pdfmetrics, TTFont)
        # 获取当前显示模式
        show_kufang = is_kufang.get()
        if show_kufang:
            pdf_headers = ["序号", "货号", "颜色", "尺码", "数量"]
            col_widths = [60, 160, 100, 100, 100]
        else:
            pdf_headers = ["序号", "货号", "颜色", "尺码", "数量", "单价", "金额", "支付", "余款"]
            col_widths = [60, 160, 100, 100, 100, 120, 120, 100, 120]
        # 先计算PDF高度
        line_height = 32
        y_table = 40 + line_height*2 + line_height*2 + line_height*3  # 标题+客户+物流+表头
        table_rows = len(items)
        y_row = y_table + line_height + table_rows*line_height
        y_sum = y_row + line_height
        pdf_height = int(y_sum + line_height)
        # 选择保存路径，默认文件名为订单号
        file_path = filedialog.asksaveasfilename(
            initialfile=f'{order_no}.pdf',
            defaultextension='.pdf',
            filetypes=[('PDF 文件', '*.pdf')],
            title='导出PDF')
        if not file_path:
            return
        c = pdfcanvas.Canvas(file_path, pagesize=(1200, pdf_height))
        # PDF内容美化：标题绿色加粗，表头灰色边框居中，内容浅灰边框居中，字体微软雅黑，金额加粗
        from reportlab.lib.colors import HexColor
        top_y = pdf_height - 40
        # 标题居中
        c.setFont(font_title, 18)
        c.setFillColor(HexColor('#2a5d2a'))
        c.drawCentredString(600, top_y, "千辉鞋业出库单")
        c.setFillColor(HexColor('#000000'))
        c.setFont(font_normal, 12)
        # 客户信息居中
        c.drawCentredString(240, top_y - line_height, f"订单号: {order_no}")
        c.drawCentredString(600, top_y - line_height, f"客户: {cust_name}")
        c.drawCentredString(960, top_y - line_height, f"地址: {cust_addr}")
        c.drawCentredString(240, top_y - line_height*2, f"出库日期: {order[7]}")
        c.drawCentredString(600, top_y - line_height*2, f"物流信息: {logistics}")
        # 表头，拉开与客户信息距离（增加额外间距）
        y_table = top_y - line_height*3 - 16  # 增加16像素间距
        x = 40
        c.setFont(font_normal, 12)
        for i, h in enumerate(pdf_headers):
            c.setStrokeColor(HexColor('#888888'))
            c.rect(x, y_table, col_widths[i], line_height, stroke=1, fill=0)
            c.setFillColor(HexColor('#000000'))
            # 表头内容居中
            c.drawCentredString(x + col_widths[i] // 2, y_table + line_height // 2, h)
            x += col_widths[i]
        # 明细
        y_row = y_table - line_height
        for idx, item in enumerate(items, 1):
            inv = dbutil.get_inventory_by_id(item[2])
            product_no = inv[2] if inv else ''
            color = inv[4] if inv else ''
            size = inv[3] if inv else ''
            quantity = item[3]
            price = item[4] if len(item) > 4 else 0.0
            amount = item[5] if len(item) > 5 else 0.0
            pay_status = "已付" if item[6]==1 else "欠款"
            debt = item[8] if len(item) > 8 else 0
            x = 40
            if show_kufang:
                row_vals = [idx, product_no, color, size, quantity]
            else:
                row_vals = [idx, product_no, color, size, quantity, f"{price:.2f}", f"{amount:.2f}", pay_status, f"{debt:.2f}"]
            for i, val in enumerate(row_vals):
                c.setStrokeColor(HexColor('#aaaaaa'))
                c.rect(x, y_row, col_widths[i], line_height, stroke=1, fill=0)
                c.setFillColor(HexColor('#000000'))
                # 金额、合计、余款加粗
                if not show_kufang and i in [5,6,8]:
                    c.setFont(font_normal, 12)
                    c.setFont(font_title, 12)
                    c.drawCentredString(x + col_widths[i] // 2, y_row + line_height // 2, str(val))
                    c.setFont(font_normal, 12)
                else:
                    c.drawCentredString(x + col_widths[i] // 2, y_row + line_height // 2, str(val))
                x += col_widths[i]
            y_row -= line_height
        # 汇总，拉近与表格底部距离（减少间距）
        y_sum = y_row - 8  # 只留8像素间距
        c.setFont(font_normal, 12)
        c.setFillColor(HexColor('#000000'))
        c.drawString(40, y_sum, f"总计数量: {int(sum(item[3] for item in items))}")
        if not show_kufang:
            c.setFont(font_title, 12)
            c.drawString(240, y_sum, f"总计金额: {total_amount:.2f}")
            c.drawString(440, y_sum, f"已缴: {total_paid:.2f}")
            c.drawString(640, y_sum, f"余款: {total_debt:.2f}")
            c.setFont(font_normal, 12)
        c.showPage()
        c.save()
        tk.messagebox.showinfo("导出成功", f"PDF已保存到：\n{file_path}")

    btn_export = ttk.Button(bottom, text="导出出库单", width=14, command=do_export)
    chk = ttk.Checkbutton(bottom, text="库房出库单", variable=is_kufang)
    def update_view():
        show_kufang = is_kufang.get()
        show_cols = ["idx", "product_no", "color", "size", "quantity"]
        if not show_kufang:
            show_cols += ["price", "amount", "item_pay_status", "debt_amount"]
        tree['displaycolumns'] = show_cols
        for w in bottom.pack_slaves():
            w.pack_forget()
        btn_export.pack(side=tk.RIGHT, padx=(0, 12))
        chk.pack(side=tk.RIGHT, padx=(0, 12))
        ttk.Label(bottom, text=f"总计数量: {int(sum(item[3] for item in items))}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
        if not show_kufang:
            ttk.Label(bottom, text=f"余款总计: {total_debt:.2f}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
            ttk.Label(bottom, text=f"已缴总计: {total_paid:.2f}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
            ttk.Label(bottom, text=f"总计金额: {total_amount:.2f}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
    chk.config(command=update_view)
    update_view()
    def print_preview_and_print():
        # 生成打印内容
        from tkinter import Toplevel, Canvas, Scrollbar
        preview = Toplevel(win)
        preview.title("打印预览")
        preview.geometry("1200x700")
        canvas = Canvas(preview, bg="white")
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vbar = Scrollbar(preview, orient=tk.VERTICAL, command=canvas.yview)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.config(yscrollcommand=vbar.set)
        # 绘制内容
        x0, y0 = 40, 40
        line_height = 32
        font_title = ("微软雅黑", 18, "bold")
        font_normal = ("微软雅黑", 12)
        canvas.create_text(x0+520, y0, text="千辉鞋业出库单", font=font_title, fill="#2a5d2a")
        y = y0 + line_height*2
        canvas.create_text(x0, y, text=f"订单号: {order_no}", font=font_normal, anchor=tk.W)
        canvas.create_text(x0+260, y, text=f"客户: {cust_name}", font=font_normal, anchor=tk.W)
        canvas.create_text(x0+480, y, text=f"地址: {cust_addr}", font=font_normal, anchor=tk.W)
        canvas.create_text(x0, y+line_height, text=f"出库日期: {order[7]}", font=font_normal, anchor=tk.W)
        canvas.create_text(x0+260, y+line_height, text=f"物流信息: {logistics}", font=font_normal, anchor=tk.W)
        # 根据库房出库单选择显示字段
        show_kufang = is_kufang.get() if 'is_kufang' in locals() or 'is_kufang' in globals() else True
        if show_kufang:
            headers = ["序号", "货号", "颜色", "尺码", "数量"]
            col_widths = [60, 160, 100, 100, 100]
        else:
            headers = ["序号", "货号", "颜色", "尺码", "数量", "单价", "金额", "支付", "余款"]
            col_widths = [60, 160, 100, 100, 100, 120, 120, 100, 120]
        # 表头
        y_table = y + line_height*3
        x = x0
        for i, h in enumerate(headers):
            canvas.create_rectangle(x, y_table, x+col_widths[i], y_table+line_height, outline="#888")
            canvas.create_text(x+col_widths[i]//2, y_table+line_height//2, text=h, font=font_normal)
            x += col_widths[i]
        # 表格内容
        y_row = y_table + line_height
        for idx, item in enumerate(items, 1):
            inv = dbutil.get_inventory_by_id(item[2])
            product_no = inv[2] if inv else ''
            color = inv[4] if inv else ''
            size = inv[3] if inv else ''
            quantity = item[3]
            price = item[4] if len(item) > 4 else 0.0
            amount = item[5] if len(item) > 5 else 0.0
            pay_status = "已付" if item[6]==1 else "欠款"
            debt = item[8] if len(item) > 8 else 0
            x = x0
            if show_kufang:
                row_vals = [idx, product_no, color, size, quantity]
            else:
                row_vals = [idx, product_no, color, size, quantity, f"{price:.2f}", f"{amount:.2f}", pay_status, f"{debt:.2f}"]
            for i, val in enumerate(row_vals):
                canvas.create_rectangle(x, y_row, x+col_widths[i], y_row+line_height, outline="#aaa")
                canvas.create_text(x+col_widths[i]//2, y_row+line_height//2, text=str(val), font=font_normal)
                x += col_widths[i]
            y_row += line_height
        # 汇总
        y_sum = y_row + line_height
        canvas.create_text(x0, y_sum, text=f"总计数量: {int(total_qty)}", font=font_normal, anchor=tk.W)
        if not show_kufang:
            canvas.create_text(x0+200, y_sum, text=f"总计金额: {total_amount:.2f}", font=font_normal, anchor=tk.W)
            canvas.create_text(x0+400, y_sum, text=f"已缴: {total_paid:.2f}", font=font_normal, anchor=tk.W)
            canvas.create_text(x0+600, y_sum, text=f"余款: {total_debt:.2f}", font=font_normal, anchor=tk.W)
        # 支持滚动，打印区域严格限定到表格和汇总下方
        canvas.config(scrollregion=(0,0,1200,y_sum+line_height))

        import win32print
        printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        selected_printer = tk.StringVar(value=printers[0] if printers else "")
        # 只保留导出按钮，悬浮显示在内容下方
        export_frame = ttk.Frame(preview)
        def place_export_frame():
            preview.update_idletasks()
            scrollregion = canvas.cget('scrollregion')
            try:
                _, _, _, content_bottom = map(int, scrollregion.split())
            except Exception:
                content_bottom = canvas.winfo_height()
            export_frame.place(relx=0.5, y=content_bottom+24, anchor=tk.N)
        export_frame.lift()
        preview.after(100, place_export_frame)
        def do_export():
            from tkinter import filedialog
            from reportlab.pdfgen import canvas as pdfcanvas
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import os
            # 注册中文字体，优先使用微软雅黑，其次黑体
            font_path = None
            for fname in ["msyh.ttf", "simhei.ttf"]:
                for dir in [os.getcwd(), os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")]:
                    fpath = os.path.join(dir, fname)
                    if os.path.exists(fpath):
                        font_path = fpath
                        break
                if font_path:
                    break
            if font_path:
                pdfmetrics.registerFont(TTFont("zhfont", font_path))
                font_title = "zhfont"
                font_normal = "zhfont"
            else:
                font_title = "Helvetica-Bold"
                font_normal = "Helvetica"
            # 先计算PDF高度
            line_height = 32
            y_table = 40 + line_height*2 + line_height*2 + line_height*3  # 标题+客户+物流+表头
            table_rows = len(items)
            y_row = y_table + line_height + table_rows*line_height
            y_sum = y_row + line_height
            pdf_height = int(y_sum + line_height)
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                defaultextension='.pdf',
                filetypes=[('PDF 文件', '*.pdf')],
                title='导出PDF')
            if not file_path:
                return
            c = pdfcanvas.Canvas(file_path, pagesize=(1200, pdf_height))
            # PDF内容美化：标题绿色加粗，表头灰色边框居中，内容浅灰边框居中，字体微软雅黑，金额加粗
            from reportlab.lib.colors import HexColor
            top_y = pdf_height - 40
            # 标题
            c.setFont(font_title, 18)
            c.setFillColor(HexColor('#2a5d2a'))
            c.drawString(40, top_y, "千辉鞋业出库单")
            c.setFillColor(HexColor('#000000'))
            c.setFont(font_normal, 12)
            # 客户信息
            c.drawString(40, top_y - line_height, f"订单号: {order_no}")
            c.drawString(300, top_y - line_height, f"客户: {cust_name}")
            c.drawString(520, top_y - line_height, f"地址: {cust_addr}")
            c.drawString(40, top_y - line_height*2, f"出库日期: {order[7]}")
            c.drawString(300, top_y - line_height*2, f"物流信息: {logistics}")
            # 表头，拉开与客户信息距离（增加额外间距）
            y_table = top_y - line_height*3 - 16  # 增加16像素间距
            x = 40
            c.setFont(font_normal, 12)
            for i, h in enumerate(headers):
                c.setStrokeColor(HexColor('#888888'))
                c.rect(x, y_table, col_widths[i], line_height, stroke=1, fill=0)
                c.setFillColor(HexColor('#000000'))
                c.drawCentredString(x+col_widths[i]//2, y_table+line_height//2, h)
                x += col_widths[i]
            # 明细
            y_row = y_table - line_height
            for idx, item in enumerate(items, 1):
                inv = dbutil.get_inventory_by_id(item[2])
                product_no = inv[2] if inv else ''
                color = inv[4] if inv else ''
                size = inv[3] if inv else ''
                quantity = item[3]
                price = item[4] if len(item) > 4 else 0.0
                amount = item[5] if len(item) > 5 else 0.0
                pay_status = "已付" if item[6]==1 else "欠款"
                debt = item[8] if len(item) > 8 else 0
                x = 40
                if show_kufang:
                    row_vals = [idx, product_no, color, size, quantity]
                else:
                    row_vals = [idx, product_no, color, size, quantity, f"{price:.2f}", f"{amount:.2f}", pay_status, f"{debt:.2f}"]
                for i, val in enumerate(row_vals):
                    c.setStrokeColor(HexColor('#aaaaaa'))
                    c.rect(x, y_row, col_widths[i], line_height, stroke=1, fill=0)
                    c.setFillColor(HexColor('#000000'))
                    # 金额、合计、余款加粗
                    if not show_kufang and i in [5,6,8]:
                        c.setFont(font_normal, 12)
                        c.setFont(font_title, 12)
                        c.drawCentredString(x+col_widths[i]//2, y_row+line_height//2, str(val))
                        c.setFont(font_normal, 12)
                    else:
                        c.drawCentredString(x+col_widths[i]//2, y_row+line_height//2, str(val))
                    x += col_widths[i]
                y_row -= line_height
            # 汇总，拉近与表格底部距离（减少间距）
            y_sum = y_row - 8  # 只留8像素间距
            c.setFont(font_normal, 12)
            c.setFillColor(HexColor('#000000'))
            c.drawString(40, y_sum, f"总计数量: {int(total_qty)}")
            if not show_kufang:
                c.setFont(font_title, 12)
                c.drawString(240, y_sum, f"总计金额: {total_amount:.2f}")
                c.drawString(440, y_sum, f"已缴: {total_paid:.2f}")
                c.drawString(640, y_sum, f"余款: {total_debt:.2f}")
                c.setFont(font_normal, 12)
            c.showPage()
            c.save()
            tk.messagebox.showinfo("导出成功", f"PDF已保存到：\n{file_path}")
        ttk.Button(export_frame, text="导出PDF", command=do_export).pack(side=tk.LEFT, padx=16)
    btn_export = ttk.Button(bottom, text="导出出库单", width=14, command=do_export)
    chk = ttk.Checkbutton(bottom, text="库房出库单", variable=is_kufang, command=update_view)
    # 统计数量
    total_qty = sum(item[3] for item in items)
    update_view()
