import os
import tkinter as tk
from tkinter import messagebox, filedialog
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

class PDFUtil:
    @staticmethod
    def register_fonts():
        """注册中文字体"""
        # 尝试注册多种中文字体
        font_paths = [
            # Windows系统路径
            (r"C:\Windows\Fonts\simsun.ttc", "SimSun"),       # 宋体
            (r"C:\Windows\Fonts\simhei.ttf", "SimHei"),       # 黑体
            (r"C:\Windows\Fonts\msyh.ttc", "MicrosoftYaHei"),  # 微软雅黑
            # Linux系统路径
            ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", "WenQuanYiMicroHei"),
            ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "WenQuanYiZenHei"),
            # macOS系统路径
            ("/System/Library/Fonts/PingFang.ttc", "PingFang"),
            ("/Library/Fonts/SimHei.ttf", "SimHei"),
        ]

        # 尝试加载字体
        for font_path, font_name in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    if font_name == "SimHei":
                        addMapping('SimHei', 0, 0, 'SimHei')  # 映射黑体的常规样式
                        addMapping('SimHei', 1, 0, 'SimHei')  # 映射黑体的粗体样式
                    return font_name, font_path
                except Exception as e:
                    print(f"字体注册失败: {font_path}, 错误: {e}")

        # 未找到任何字体，使用默认字体
        messagebox.showwarning("警告", "未找到中文字体，PDF中的中文可能无法正确显示。")
        return "Helvetica", None

    @staticmethod
    def create_pdf(file_path, elements, pagesize=A4, margins=(15*mm, 15*mm, 15*mm, 15*mm)):
        """
        创建PDF文件
        :param file_path: 保存路径
        :param elements: PDF内容元素列表
        :param pagesize: 页面大小，默认为A4
        :param margins: 边距 (左, 右, 上, 下)
        """
        try:
            doc = SimpleDocTemplate(
                file_path,
                pagesize=pagesize,
                leftMargin=margins[0],
                rightMargin=margins[1],
                topMargin=margins[2],
                bottomMargin=margins[3]
            )
            doc.build(elements)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"PDF生成失败: {str(e)}")
            return False

    @staticmethod
    def create_order_detail_pdf(order, items, customer, file_path=None, parent=None):
        """
        导出出库单详情PDF
        :param order: 订单信息
        :param items: 订单项列表
        :param customer: 客户信息
        :param file_path: 保存路径，默认为None（会弹出保存对话框）
        :param parent: 父窗口，用于设置对话框的层级
        """
        # 注册字体
        font_name, _ = PDFUtil.register_fonts()

        # 选择保存路径
        if not file_path:
            # 创建一个临时的顶级窗口作为对话框的父窗口
            if not parent:
                parent = tk.Toplevel()
                parent.withdraw()  # 隐藏窗口
            else:
                # 确保父窗口是顶级窗口
                while parent.master:
                    parent = parent.master

            file_path = filedialog.asksaveasfilename(
                initialfile=f'{order.get("order_no", "订单")}.pdf',
                defaultextension='.pdf',
                filetypes=[('PDF 文件', '*.pdf')],
                title='导出PDF',
                parent=parent
            )
            if not file_path:
                return False

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

        # 客户信息 - 第一行：单号、客户、地址
        order_no = order.get('order_no', '')
        cust_name = customer[1] if customer else f"ID:{order.get('customer_id', '')}"
        cust_addr = customer[2] if customer else ""
        outbound_date = order.get('outbound_date', '')[:10]
        logistics = customer[4] if customer else ""

        # 第一行信息（三项均匀分布）
        first_line_data = [
            f"单号：{order_no}",
            f"客户：{cust_name}",
            f"地址：{cust_addr}"
        ]
        first_line_table = Table([first_line_data], colWidths=[60*mm, 60*mm, 60*mm], hAlign='CENTER')
        first_line_table.setStyle(TableStyle([
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTNAME", (0,0), (-1,-1), font_name),
            ("FONTSIZE", (0,0), (-1,-1), 11),
        ]))
        elements.append(first_line_table)

        # 第二行信息（物流与单号对齐，日期与地址对齐）
        second_line_data = [
            f"物流：{logistics or ''}",
            "",  # 空列，用于对齐客户信息
            f"日期：{outbound_date}"
        ]
        second_line_table = Table([second_line_data], colWidths=[60*mm, 60*mm, 60*mm], hAlign='CENTER')
        second_line_table.setStyle(TableStyle([
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTNAME", (0,0), (-1,-1), font_name),
            ("FONTSIZE", (0,0), (-1,-1), 11),
        ]))
        elements.append(second_line_table)

        # 添加show_kufang变量定义
        show_kufang = order.get('show_kufang', True)

        # 根据视图类型设置表头和列宽
        if show_kufang:
            product_header = ["序号", "货号", "颜色", "单位", "尺码", "数量"]
            col_widths = [12*mm, 30*mm, 18*mm, 13*mm, 18*mm, 22*mm]
        else:
            product_header = ["序号", "货号", "颜色", "单位", "尺码", "数量", "单价", "金额"]
            col_widths = [12*mm, 30*mm, 18*mm, 13*mm, 18*mm, 22*mm, 15*mm, 18*mm]

        product_data = [product_header]
        total_quantity = 0
        total_amount = 0.0
        order_remark = order.get('remark', '无')  # 获取订单备注
        for idx, item in enumerate(items, 1):
            product_no = item.get('product_no', '')
            color = item.get('color', '')
            unit = item.get('unit', '')
            size = item.get('size', '')
            quantity = item.get('quantity', 0)
            price = item.get('price', 0.0)
            amount = item.get('amount', 0.0)
            remark = item.get('remark', '')
            total_quantity += quantity
            total_amount += amount
            
            if show_kufang:
                product_data.append([idx, product_no, color, unit, size, quantity])
            else:
                product_data.append([idx, product_no, color, unit, size, quantity, f"{price:.2f}", f"{amount:.2f}"])

        # 汇总区 - 添加到产品数据表格中（明细下方，备注上方）
        total_paid = order.get('total_paid', 0.0)
        total_debt = order.get('total_debt', 0.0)
        # 根据视图类型设置汇总信息
        merged_remark = f"备注：{order_remark}"
        if show_kufang:
            # 6列布局的汇总行（合并所有列）
            product_data.append([f'总计数量：{total_quantity}'] + [''] * 5)
            product_data.append([merged_remark] + [''] * 5)
        else:
            # 8列布局的汇总行（合并所有列）
            summary_text = (
                f'总计数量：{total_quantity}    '
                f'总计金额：{total_amount:.2f}    '
                f'已付金额：{total_paid:.2f}    '
                f'未支付金额：{total_debt:.2f}'
            )
            product_data.append([summary_text] + [''] * 7)
            product_data.append([merged_remark] + [''] * 7)

        product_table = Table(product_data, colWidths=col_widths, hAlign='CENTER')
        product_table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TEXTCOLOR", (0,0), (-1,0), colors.black),
            ("FONTNAME", (0,0), (-1,-1), font_name),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            # 设置汇总行样式
            ("FONTNAME", (0,-2), (-1,-2), font_name),
            ("FONTSIZE", (0,-2), (-1,-2), 10),
            ("BOTTOMPADDING", (0,-2), (-1,-2), 5),
            ("ALIGN", (0,-2), (-1,-2), "LEFT"),
            # 合并汇总行所有单元格（倒数第二行）
            ("SPAN", (0,-2), (-1,-2)),

            # 设置备注行样式
            ("ALIGN", (0,-1), (-1,-1), "LEFT"),  # 备注文字左对齐
            # 合并备注行所有单元格
            ("SPAN", (0,-1), (-1,-1)),  # 合并从第一列到最后一列
        ]))
        elements.append(product_table)

        # 签字区
        sign_data = [["制单人：", "出库：", "送货人：", "收货人："]]
        sign_table = Table(sign_data, colWidths=[38*mm]*5, hAlign='CENTER')
        sign_table.setStyle(TableStyle([
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTNAME", (0,0), (-1,-1), font_name),
            ("FONTSIZE", (0,0), (-1,-1), 10),
        ]))
        elements.append(sign_table)

        # 生成PDF
        return PDFUtil.create_pdf(file_path, elements)

    @staticmethod
    def create_customer_statement_pdf(statement_data, file_path=None, parent=None):
        """
        导出客户对账单PDF
        :param statement_data: 对账单数据
        :param file_path: 保存路径，默认为None（会弹出保存对话框）
        :param parent: 父窗口，用于设置对话框的层级
        """
        # 注册字体
        font_name, _ = PDFUtil.register_fonts()

        # 选择保存路径
        if not file_path:
            # 创建一个临时的顶级窗口作为对话框的父窗口
            if not parent:
                parent = tk.Toplevel()
                parent.withdraw()  # 隐藏窗口
            else:
                # 确保父窗口是顶级窗口
                while parent.master:
                    parent = parent.master

            # 保存原始topmost状态
            original_topmost = parent.attributes('-topmost') if hasattr(parent, 'attributes') else False
            try:
                # 临时将父窗口的topmost设置为False，以便文件对话框能显示在顶层
                parent.attributes('-topmost', False)

                file_path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf")],
                    title="导出对账单",
                    parent=parent
                )
            finally:
                # 恢复父窗口的原始topmost状态
                if hasattr(parent, 'attributes'):
                    parent.attributes('-topmost', original_topmost)

            if not file_path:
                return False

        # 构建PDF内容
        elements = []
        styles = getSampleStyleSheet()

        # 修改标题样式使用中文字体
        styles.add(ParagraphStyle(name='CNTitle', fontName=font_name, fontSize=18, alignment=1, leading=24))
        styles.add(ParagraphStyle(name='CNNormal', fontName=font_name, fontSize=11, leading=16))
        styles.add(ParagraphStyle(name='CNBold', fontName=font_name, fontSize=11, leading=16, bold=True))

        # 添加标题
        elements.append(Paragraph("千辉鞋业-客户对账单", styles['CNTitle']))
        elements.append(Spacer(1, 12))

        # 客户信息和日期区域
        customer_info = [
            [f"客户: {statement_data['customer_name']}", f"账单周期: {statement_data['bill_period']}", f"出账日期: {statement_data['issue_date']}"]
        ]
        customer_info_table = Table(customer_info, colWidths=[90, 200, 120], hAlign='CENTER')
        customer_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(customer_info_table)
        elements.append(Spacer(1, 8))

        # 金额信息区域
        amount_info = [
            [
                f"往期欠款: {statement_data['previous_debt']:.2f}", 
                f"本期欠款: {statement_data['current_debt']:.2f}", 
                f"总计金额: {statement_data['total_amount']:.2f}"
            ]
        ]
        amount_info_table = Table(amount_info, colWidths=[100, 100, 100])
        amount_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(amount_info_table)
        elements.append(Spacer(1, 12))

        # 订单表格
        headers = ["订单号", "出库日期", "货号", "颜色", "单位", "尺码", "数量", "单价", "金额"]
        table_data = [headers] + statement_data['orders']
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('ALIGN', (7, 1), (8, -1), 'RIGHT'),  # 单价和金额靠右对齐
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        # 总计金额行
        total_amount = statement_data['total_amount']
        upper_total = statement_data['upper_total']
        total_info = [
            [f"应付总金额: {total_amount:.2f}"],
            [f"大写: {upper_total}"]
        ]
        total_info_table = Table(total_info, colWidths=[300])
        total_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (0, 0), 12),
            ('FONTSIZE', (0, 1), (0, 1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('BOLDFONT', (0, 0), (0, 0), 1),
        ]))
        elements.append(total_info_table)

        # 生成PDF
        return PDFUtil.create_pdf(file_path, elements)

    @staticmethod
    def create_table(data, style=None, col_widths=None):
        """
        创建PDF表格
        :param data: 表格数据
        :param style: 表格样式
        :param col_widths: 列宽
        :return: Table对象
        """
        table = Table(data, colWidths=col_widths)
        if style:
            table.setStyle(style)
        return table

    @staticmethod
    def get_sample_style_sheet():
        """获取样式表"""
        styles = getSampleStyleSheet()
        return styles

    @staticmethod
    def create_paragraph(text, style=None):
        """
        创建段落
        :param text: 文本内容
        :param style: 段落样式
        :return: Paragraph对象
        """
        return Paragraph(text, style)

    @staticmethod
    def create_spacer(width, height):
        """
        创建间隔
        :param width: 宽度
        :param height: 高度
        :return: Spacer对象
        """
        return Spacer(width, height)