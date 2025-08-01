import tkinter as tk
from tkinter import ttk
from util import dbutil
import tkinter.simpledialog
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

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
        
        # 注册中文字体
        def register_font():
            # 系统字体路径
            system_font_paths = [
                # Windows系统
                r"C:\Windows\Fonts\simsun.ttc",  # 宋体
                r"C:\Windows\Fonts\simhei.ttf",  # 黑体
                r"C:\Windows\Fonts\msyh.ttc",    # 微软雅黑
                # Linux系统
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # 文泉驿微米黑
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",    # 文泉驿正黑
                # macOS系统
                "/System/Library/Fonts/PingFang.ttc",              # 苹方
                "/Library/Fonts/SimHei.ttf",                       # 黑体
            ]
            
            # 检查系统字体
            for font_path in system_font_paths:
                if os.path.exists(font_path):
                    try:
                        font_name = os.path.basename(font_path).split('.')[0]
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        return font_name
                    except Exception as e:
                        print(f"字体注册失败: {font_path}, 错误: {e}")
            
            # 尝试使用相对路径的字体
            relative_fonts = [
                "simsun.ttf", "simhei.ttf", "msyh.ttf", 
                "fonts/simsun.ttf", "fonts/simhei.ttf", "fonts/msyh.ttf"
            ]
            for font_name in relative_fonts:
                if os.path.exists(font_name):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name.split('.')[0], font_name))
                        return font_name.split('.')[0]
                    except Exception as e:
                        print(f"字体注册失败: {font_name}, 错误: {e}")
            
            # 未找到任何字体，使用默认字体
            tk.messagebox.showwarning("警告", "未找到中文字体，PDF中的中文可能无法正确显示。")
            return "Helvetica"
        
        # 注册字体
        font_name = register_font()
        
        # 选择保存路径，默认文件名为订单号
        file_path = filedialog.asksaveasfilename(
            initialfile=f'{order_no}.pdf',
            defaultextension='.pdf',
            filetypes=[('PDF 文件', '*.pdf')],
            title='导出PDF')
        if not file_path:
            return
        
        # 构建PDF内容
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            topMargin=8*mm,
            bottomMargin=15*mm,
            leftMargin=15*mm,
            rightMargin=15*mm
        )
        elements = []
        styles = getSampleStyleSheet()
        
        # 新建支持中文的样式
        styles.add(ParagraphStyle(name='CNTitle', fontName=font_name, fontSize=20, alignment=1, leading=24))
        styles.add(ParagraphStyle(name='CNNormal', fontName=font_name, fontSize=11, leading=16))
        styles.add(ParagraphStyle(name='CNSmall', fontName=font_name, fontSize=10, leading=14))
        
        # 标题
        title = Paragraph("千辉鞋业销售单", styles['CNTitle'])
        elements.append(title)
        
        # 客户信息区合并为一个单元格，无表格线
        customer_info_text = (
            f"客户名称：{cust_name}    客户地址：{cust_addr}    联系电话：{cust[3] if cust else ''}    日  期：{order[7][:10]}\n"
            
            f"物流信息：{logistics or ''}"
        )
        customer_info_table = Table([[customer_info_text]], colWidths=[180*mm], hAlign='LEFT')
        customer_info_table.setStyle(TableStyle([
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTNAME", (0,0), (-1,-1), font_name),
            ("FONTSIZE", (0,0), (-1,-1), 11),
            # 不设置GRID
        ]))
        elements.append(customer_info_table)
        
        # 产品明细表格
        show_kufang = is_kufang.get()
        if show_kufang:
            product_header = ["序号", "货号", "颜色", "尺码", "数量", "备注"]
            col_widths = [12*mm, 30*mm, 18*mm, 18*mm, 22*mm, 15*mm]
        else:
            product_header = ["序号", "货号", "颜色", "尺码", "数量", "单价", "金额", "支付", "余款", "备注"]
            col_widths = [12*mm, 22*mm, 18*mm, 18*mm, 18*mm, 13*mm, 22*mm, 18*mm, 18*mm, 30*mm]

        product_data = [product_header]
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
            # 备注字段，数据库如有可填，否则留空
            remark = ""
            if show_kufang:
                row_vals = [idx, product_no, color, size, quantity, remark]
            else:
                row_vals = [idx, product_no, color, size, quantity, f"{price:.2f}", f"{amount:.2f}", pay_status, f"{debt:.2f}", remark]
            product_data.append(row_vals)

        product_table = Table(product_data, colWidths=col_widths, hAlign='LEFT')
        product_table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),  # 内容居中
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TEXTCOLOR", (0,0), (-1,0), colors.black),
            ("FONTNAME", (0,0), (-1,-1), font_name),
            ("FONTSIZE", (0,0), (-1,-1), 10),
        ]))
        elements.append(product_table)
        
        # 汇总区
        if show_kufang:
            summary_text = f"总计数量：{int(sum(item[3] for item in items))}"
        else:
            summary_text = (
                f"总计数量：{int(sum(item[3] for item in items))}    "
                f"总计金额：{total_amount:.2f}    "
                f"已缴：{total_paid:.2f}    "
                f"余款：{total_debt:.2f}"
            )
        # 合并为一个单元格，无表格线
        total_info_table = Table([[summary_text]], colWidths=[180*mm], hAlign='LEFT')
        total_info_table.setStyle(TableStyle([
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTNAME", (0,0), (-1,-1), font_name),
            ("FONTSIZE", (0,0), (-1,-1), 11),
            # 不设置GRID
        ]))
        elements.append(total_info_table)
        
        # 签字区
        sign_data = [["制单人：", "出库：", "送货人：", "收货人："]]
        sign_table = Table(sign_data, colWidths=[38*mm]*5)
        sign_table.setStyle(TableStyle([
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTNAME", (0,0), (-1,-1), font_name),
            ("FONTSIZE", (0,0), (-1,-1), 10),
        ]))
        elements.append(sign_table)
        
        # 生成PDF
        doc.build(elements)
        tk.messagebox.showinfo("导出成功", f"PDF已保存到：\n{file_path}")

    def update_view():
        show_kufang = is_kufang.get()
        show_cols = ["idx", "product_no", "color", "size", "quantity"]
        if not show_kufang:
            show_cols += ["price", "amount", "item_pay_status", "debt_amount"]
        tree['displaycolumns'] = show_cols
        for w in bottom.pack_slaves():
            w.pack_forget()
        chk.pack(side=tk.RIGHT, padx=(0, 12))
        btn_export.pack(side=tk.RIGHT, padx=(0, 12))
        ttk.Label(bottom, text=f"总计数量: {int(sum(item[3] for item in items))}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
        if not show_kufang:
            ttk.Label(bottom, text=f"余款总计: {total_debt:.2f}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
            ttk.Label(bottom, text=f"已缴总计: {total_paid:.2f}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))
            ttk.Label(bottom, text=f"总计金额: {total_amount:.2f}", font=("微软雅黑", 11, "bold")).pack(side=tk.RIGHT, padx=(0, 18))

    btn_export = ttk.Button(bottom, text="导出出库单", width=14, command=do_export)
    chk = ttk.Checkbutton(bottom, text="库房出库单", variable=is_kufang, command=update_view)
    update_view()    