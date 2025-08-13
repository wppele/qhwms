import tkinter as tk
from tkinter import ttk, messagebox
from util.dbutil import get_order_details, get_statements, delete_statement_by_ids
import os
from util.pdfutil import PDFUtil
from util.utils import center_window

class CustomerStatementPage(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.create_widgets()
        self.refresh()

    def create_widgets(self):
        # 顶部筛选区域
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        # 客户名称筛选
        ttk.Label(filter_frame, text="客户名称:").pack(side=tk.LEFT, padx=5)
        self.customer_entry = ttk.Entry(filter_frame, width=20)
        self.customer_entry.pack(side=tk.LEFT, padx=5)

        # 筛选按钮
        ttk.Button(filter_frame, text="筛选", command=self.refresh).pack(side=tk.LEFT, padx=5)

        # 刷新按钮
        ttk.Button(filter_frame, text="刷新", command=self.refresh).pack(side=tk.LEFT, padx=5)

        # 删除按钮
        ttk.Button(filter_frame, text="删除", command=self.delete_statement).pack(side=tk.LEFT, padx=5)

        # Treeview表格
        columns = ("id", "statement_no", "customer_name", "outbound_ids", "previous_debt", "current_debt", "total_amount", "bill_period", "issue_date")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)

        # 设置列标题和宽度
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=50, anchor=tk.CENTER)

        self.tree.heading("statement_no", text="对账单号")
        self.tree.column("statement_no", width=120, anchor=tk.CENTER)

        self.tree.heading("customer_name", text="客户名称")
        self.tree.column("customer_name", width=150, anchor=tk.CENTER)

        self.tree.heading("outbound_ids", text="订单ID")
        self.tree.column("outbound_ids", width=100, anchor=tk.CENTER)

        self.tree.heading("previous_debt", text="往期欠款")
        self.tree.column("previous_debt", width=100, anchor=tk.E)

        self.tree.heading("current_debt", text="本期欠款")
        self.tree.column("current_debt", width=100, anchor=tk.E)

        self.tree.heading("total_amount", text="总计金额")
        self.tree.column("total_amount", width=100, anchor=tk.E)

        self.tree.heading("bill_period", text="账单周期")
        self.tree.column("bill_period", width=150, anchor=tk.CENTER)

        self.tree.heading("issue_date", text="出账日期")
        self.tree.column("issue_date", width=100, anchor=tk.CENTER)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 绑定双击事件查看详情
        self.tree.bind("<Double-1>", self.on_double_click)

        # 鼠标悬停表格项时显示提示
        def show_tooltip(event):
            widget = event.widget
            row_id = widget.identify_row(event.y)
            if row_id:
                if not hasattr(widget, '_tooltip_label'):
                    widget._tooltip_label = tk.Label(widget, text="双击查看详情", bg="#ffffe0", fg="#333", font=("微软雅黑", 10), relief=tk.SOLID, bd=1)
                widget._tooltip_label.place_forget()
                widget._tooltip_label.place(x=event.x, y=event.y+18)
            else:
                if hasattr(widget, '_tooltip_label'):
                    widget._tooltip_label.place_forget()
        def hide_tooltip(event):
            widget = event.widget
            if hasattr(widget, '_tooltip_label'):
                widget._tooltip_label.place_forget()
        self.tree.bind('<Motion>', show_tooltip)
        self.tree.bind('<Leave>', hide_tooltip)

    def show_tooltip(self, event):
        # 获取鼠标位置
        x, y = event.x_root, event.y_root
        # 显示提示框，位置稍微偏移鼠标
        self.tooltip.place(x=x+10, y=y+10)

    def delete_statement(self):
        # 获取选中的项
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请选择要删除的对账单！")
            return

        # 确认删除
        if not messagebox.askyesno("确认", "确定要删除选中的对账单吗？"):
            return

        # 获取选中项的ID
        statement_ids = []
        for item in selected_items:
            values = self.tree.item(item, "values")
            statement_ids.append(values[0])  # 假设第一列是ID

        # 删除数据库中的记录
        try:
            deleted_count = delete_statement_by_ids(statement_ids)
            messagebox.showinfo("成功", f"已成功删除 {deleted_count} 份对账单！")
            # 刷新表格
            self.refresh()
        except Exception as e:
            messagebox.showerror("错误", f"删除对账单失败: {str(e)}")

    def refresh(self):
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 获取筛选条件
        customer_name = self.customer_entry.get().strip()

        try:
            # 使用dbutil中的函数获取对账单数据
            rows = get_statements(customer_name)

            # 插入数据到表格
            for row in rows:
                self.tree.insert('', 'end', values=row)
        except Exception as e:
            messagebox.showerror("错误", f"查询对账单数据失败: {str(e)}")

    def on_double_click(self, event):
        # 获取选中的项
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return

        # 获取选中项的值
        values = self.tree.item(item, "values")
        if not values:
            return

        # 获取订单详情
        order_details = self.get_order_details(values[3])

        # 创建详情对话框，设置为主窗口的子窗口
        detail_window = tk.Toplevel(self.parent)
        detail_window.title("千辉鞋业-客户对账单")
        detail_window.resizable(True, True)

        # 设置为父窗口的临时窗口，避免成为独立顶级窗口
        detail_window.transient(self.parent)
        # 使用utils中的方法居中显示
        center_window(detail_window, 900, 600)

        # 创建标签显示详情
        frame = ttk.Frame(detail_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # 顶部标题
        ttk.Label(frame, text="千辉鞋业-客户对账单", font=("微软雅黑", 18, "bold")).pack(pady=10)

        # 客户信息和日期区域（标签和内容合并到一个单元格）
        info_frame1 = ttk.Frame(frame)
        info_frame1.pack(fill=tk.X, pady=5)

        # 客户名称
        ttk.Label(info_frame1, text=f"客户名称: {values[2]}", font=("微软雅黑", 10, "bold"), anchor=tk.W).grid(row=0, column=0, padx=5, sticky="w")

        # 账单周期
        ttk.Label(info_frame1, text=f"账单周期: {values[7]}", anchor=tk.W).grid(row=0, column=1, padx=5, sticky="w")

        # 出账日期
        ttk.Label(info_frame1, text=f"出账日期: {values[8]}", anchor=tk.W).grid(row=0, column=2, padx=5, sticky="w")

        # 金额信息区域（标签和内容合并到一个单元格并靠右对齐）
        info_frame2 = ttk.Frame(frame)
        info_frame2.pack(fill=tk.X, pady=5)

        # 往期欠款
        ttk.Label(info_frame2, text=f"往期欠款: {float(values[4]):.2f}", foreground="red", anchor=tk.E).grid(row=0, column=0, padx=5, sticky="e", ipadx=20)

        # 本期欠款
        ttk.Label(info_frame2, text=f"本期欠款: {float(values[5]):.2f}", foreground="red", anchor=tk.E).grid(row=0, column=1, padx=5, sticky="e", ipadx=20)

        # 总计金额
        ttk.Label(info_frame2, text=f"总计金额: {float(values[6]):.2f}", foreground="red", font=("微软雅黑", 10, "bold"), anchor=tk.E).grid(row=0, column=2, padx=5, sticky="e", ipadx=20)

        # 订单表格
        columns = ("order_no", "outbound_date", "product_no", "color", "unit", "size", "quantity", "price", "amount")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)

        # 设置列标题和宽度
        tree.heading("order_no", text="订单号")
        tree.column("order_no", width=100, anchor=tk.CENTER)

        tree.heading("outbound_date", text="出库日期")
        tree.column("outbound_date", width=100, anchor=tk.CENTER)

        tree.heading("product_no", text="货号")
        tree.column("product_no", width=100, anchor=tk.CENTER)

        tree.heading("color", text="颜色")
        tree.column("color", width=80, anchor=tk.CENTER)

        tree.heading("unit", text="单位")
        tree.column("unit", width=60, anchor=tk.CENTER)

        tree.heading("size", text="尺码")
        tree.column("size", width=60, anchor=tk.CENTER)

        tree.heading("quantity", text="数量")
        tree.column("quantity", width=60, anchor=tk.CENTER)

        tree.heading("price", text="单价")
        tree.column("price", width=80, anchor=tk.E)

        tree.heading("amount", text="金额")
        tree.column("amount", width=100, anchor=tk.E)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # 插入订单详情数据
        for item in order_details:
            tree.insert('', 'end', values=item)

        # 布局调整：创建主容器
        main_container = ttk.Frame(frame)
        main_container.pack(fill=tk.X, pady=10)

        # 按钮区域放到左侧
        btn_frame = ttk.Frame(main_container)
        btn_frame.pack(side=tk.LEFT, padx=10)

        # 导出PDF按钮
        ttk.Button(btn_frame, text="导出PDF", command=lambda: self.export_to_pdf(values, order_details, detail_window)).pack(pady=5, fill=tk.X)

        # 关闭按钮
        ttk.Button(btn_frame, text="关闭", command=detail_window.destroy).pack(pady=5, fill=tk.X)

        # 总计金额行放到右侧
        total_frame = ttk.Frame(main_container)
        total_frame.pack(side=tk.RIGHT, padx=10)

        total_amount = float(values[6])
        upper_total = self.convert_to_upper(total_amount)

        # 合并label和内容到一个单元格，并靠右对齐
        ttk.Label(total_frame, text=f"应付总金额: {total_amount:.2f}", foreground="red", font=('微软雅黑', 12, 'bold'), anchor=tk.E).grid(row=0, column=0, padx=10, pady=2, sticky='e')
        ttk.Label(total_frame, text=f"大写: {upper_total}", foreground="red", font=('微软雅黑', 10, 'bold'), anchor=tk.E).grid(row=1, column=0, padx=10, pady=2, sticky='e')

    def get_order_details(self, outbound_ids):
        """
        根据订单ID获取订单详情
        :param outbound_ids: 订单ID字符串，多个ID用逗号分隔
        :return: 订单详情列表
        """
        ids = outbound_ids.split(',') if outbound_ids else []
        return get_order_details(ids)

    def convert_to_upper(self, amount):
        """
        将金额转换为大写
        :param amount: 金额
        :return: 大写金额字符串
        """
        digits = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
        units = ['元', '拾', '佰', '仟', '万', '拾', '佰', '仟', '亿', '拾', '佰', '仟']
        dec_units = ['角', '分']

        # 处理整数和小数部分
        integer_part = int(amount)
        decimal_part = int(round((amount - integer_part) * 100))

        # 转换整数部分
        result = ''
        if integer_part == 0:
            result = '零'
        else:
            integer_str = str(integer_part)
            for i in range(len(integer_str)):
                digit = int(integer_str[i])
                position = len(integer_str) - i - 1
                if digit != 0:
                    result += digits[digit] + units[position]
                else:
                    # 处理零
                    if i > 0 and int(integer_str[i-1]) != 0:
                        result += '零'
                    # 处理万和亿单位
                    if position in [4, 8] and integer_part >= 10**position:
                        result += units[position]

        # 添加元
        result += '元'

        # 处理小数部分
        if decimal_part == 0:
            result += '整'
        else:
            jiao = decimal_part // 10
            fen = decimal_part % 10
            if jiao != 0:
                result += digits[jiao] + dec_units[0]
            else:
                result += '零'
            if fen != 0:
                result += digits[fen] + dec_units[1]

        return result

    def export_to_pdf(self, statement_data, order_details, parent=None):
        """
        导出对账单到PDF
        :param statement_data: 对账单数据
        :param order_details: 订单详情数据
        :param parent: 父窗口，用于设置对话框的层级
        """
        # 准备数据
        customer_name = statement_data[2]
        bill_period = statement_data[7]
        issue_date = statement_data[8]
        previous_debt = float(statement_data[4])
        current_debt = float(statement_data[5])
        total_amount = float(statement_data[6])
        upper_total = self.convert_to_upper(total_amount)

        # 格式化订单详情数据
        formatted_orders = []
        for item in order_details:
            formatted_orders.append([
                item[0],  # 订单号
                item[1],  # 出库日期
                item[2],  # 货号
                item[3],  # 颜色
                item[4],  # 单位
                item[5],  # 尺码
                item[6],  # 数量
                item[7],  # 单价
                item[8]   # 金额
            ])

        # 准备PDF数据，与对账单详情对话框格式一致
        pdf_data = {
            'customer_name': customer_name,
            'bill_period': bill_period,
            'issue_date': issue_date,
            'previous_debt': previous_debt,
            'current_debt': current_debt,
            'total_amount': total_amount,
            'upper_total': upper_total,
            'orders': formatted_orders
        }

        # 调用PDF工具生成对账单
        PDFUtil.create_customer_statement_pdf(pdf_data, parent=parent)