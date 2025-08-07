import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from util import dbutil
from util.pdfutil import PDFUtil
import os
# 尝试导入tkcalendar，如果不存在则提供回退方案
try:
    from tkcalendar import DateEntry
    has_tkcalendar = True
except ImportError:
    has_tkcalendar = False

class ArrearsSettlePage(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()
        self.refresh()

    def create_widgets(self):
        # 筛选区
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(filter_frame, text="订单号:").pack(side=tk.LEFT)
        self.search_order_no = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.search_order_no, width=16).pack(side=tk.LEFT, padx=4)
        ttk.Label(filter_frame, text="客户:").pack(side=tk.LEFT)
        self.search_customer = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.search_customer, width=14).pack(side=tk.LEFT, padx=4)
        # 添加日期区间筛选
        ttk.Label(filter_frame, text="日期:").pack(side=tk.LEFT, padx=(10,0))
        self.start_date = tk.StringVar()
        if has_tkcalendar:
            self.start_date_entry = DateEntry(filter_frame, textvariable=self.start_date, width=10, date_pattern='yyyy-mm-dd')
            self.start_date_entry.pack(side=tk.LEFT, padx=4)
        else:
            ttk.Entry(filter_frame, textvariable=self.start_date, width=12).pack(side=tk.LEFT, padx=4)
            ttk.Label(filter_frame, text="(格式: yyyy-mm-dd)", font=('Arial', 8)).pack(side=tk.LEFT)

        ttk.Label(filter_frame, text="-").pack(side=tk.LEFT)
        self.end_date = tk.StringVar()
        if has_tkcalendar:
            self.end_date_entry = DateEntry(filter_frame, textvariable=self.end_date, width=10, date_pattern='yyyy-mm-dd')
            self.end_date_entry.pack(side=tk.LEFT, padx=4)
        else:
            ttk.Entry(filter_frame, textvariable=self.end_date, width=12).pack(side=tk.LEFT, padx=4)
            ttk.Label(filter_frame, text="(格式: yyyy-mm-dd)", font=('Arial', 8)).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="筛选", command=self.refresh, width=8).pack(side=tk.LEFT, padx=8)
        ttk.Button(filter_frame, text="导出对账单", command=self.export_statement_pdf, width=10).pack(side=tk.RIGHT, padx=8)
        columns = ("serial", "order_no", "customer_name", "total_amount", "total_paid", "remaining_debt", "outbound_date")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("serial", text="序号")
        self.tree.heading("order_no", text="订单号")
        self.tree.heading("customer_name", text="客户")
        self.tree.heading("total_amount", text="订单金额")
        self.tree.heading("total_paid", text="已付金额")
        self.tree.heading("remaining_debt", text="欠款金额")
        self.tree.heading("outbound_date", text="出库日期")
        self.tree.column("serial", width=60, anchor=tk.CENTER)
        self.tree.column("order_no", width=140, anchor=tk.CENTER)
        self.tree.column("customer_name", width=120, anchor=tk.CENTER)
        self.tree.column("total_amount", width=100, anchor=tk.CENTER)
        self.tree.column("total_paid", width=100, anchor=tk.CENTER)
        self.tree.column("remaining_debt", width=100, anchor=tk.CENTER)
        self.tree.column("outbound_date", width=120, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # 鼠标悬停表格项时显示提示
        def show_tooltip(event):
            widget = event.widget
            row_id = widget.identify_row(event.y)
            if row_id:
                if not hasattr(widget, '_tooltip_label'):
                    widget._tooltip_label = tk.Label(widget, text="双击结算", bg="#ffffe0", fg="#333", font=("微软雅黑", 10), relief=tk.SOLID, bd=1)
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
        self.tree.bind('<Double-1>', self.on_double_click)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        order_no_kw = getattr(self, 'search_order_no', tk.StringVar()).get().strip() if hasattr(self, 'search_order_no') else ''
        customer_kw = getattr(self, 'search_customer', tk.StringVar()).get().strip() if hasattr(self, 'search_customer') else ''
        start_date_kw = getattr(self, 'start_date', tk.StringVar()).get().strip() if hasattr(self, 'start_date') else ''
        end_date_kw = getattr(self, 'end_date', tk.StringVar()).get().strip() if hasattr(self, 'end_date') else ''
        debts = dbutil.get_all_debt_records()
        # debts: (debt_id, outbound_id, item_ids, remaining_debt)
        # 需要查客户姓名和订单号
        idx = 1
        for debt in debts:
            debt_id, outbound_id, item_ids, remaining_debt = debt
            # 查找订单号和客户名
            order = dbutil.get_outbound_order_by_id(outbound_id)
            if order:
                order_no = order[1]
                customer_id = order[2]
                # 查客户名
                customer = dbutil.get_customer_by_id(customer_id)
                customer_name = customer[1] if customer else ""
            else:
                order_no = ""
                customer_name = ""
            # 格式化日期，只显示年月日
            outbound_date = order[7].split(' ')[0] if order and len(order) > 7 else ''
            # 筛选逻辑
            if order_no_kw and order_no_kw not in str(order_no):
                continue
            if customer_kw and customer_kw not in str(customer_name):
                continue
            # 日期区间筛选
            if outbound_date:
                if start_date_kw and outbound_date < start_date_kw:
                    continue
                if end_date_kw and outbound_date > end_date_kw:
                    continue
            # 格式化日期，只显示年月日
            outbound_date = order[7].split(' ')[0] if order and len(order) > 7 else ''
            # 获取订单金额和已付金额
            # 处理可能的非数值total_amount
            try:
                total_amount = float(order[3]) if order and len(order) > 3 else 0.0
            except (ValueError, TypeError):
                total_amount = 0.0
            total_paid = order[5] if order and len(order) > 5 else 0.0
            self.tree.insert('', tk.END, values=(
                idx, 
                order_no, 
                customer_name, 
                f"{total_amount:.2f}", 
                f"{total_paid:.2f}", 
                f"{remaining_debt:.2f}", 
                outbound_date
            ), tags=(f"{debt_id}|{outbound_id}|{item_ids}",))
            idx += 1

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        # 通过tag获取真实debt_id, outbound_id, item_ids
        tag = self.tree.item(selected[0]).get('tags', ('',))[0]
        try:
            debt_id, outbound_id, item_ids = tag.split('|', 2)
        except Exception:
            messagebox.showerror("错误", "无法获取欠账记录ID")
            return
        # 处理可能的非数值remaining_debt
        try:
            remaining_debt = float(item['values'][5])
        except (ValueError, TypeError):
            remaining_debt = 0.0
        if remaining_debt <= 0:
            messagebox.showinfo("提示", "该欠款已结清！")
            return
        # 自定义对话框：金额+支付方式
        pay_amount, pay_method = self.ask_amount_and_method(remaining_debt)
        if pay_amount is None or not pay_method:
            return
        # 写入payment_record
        from datetime import datetime
        dbutil.insert_payment_record(outbound_id, item_ids, pay_amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pay_method)
        # 更新debt_record
        new_debt = float(remaining_debt) - float(pay_amount)
        # 同步更新出库单主表和明细表的已付/待付金额
        self.update_outbound_payment_status(outbound_id)
        if new_debt <= 0.01:
            self.delete_debt_record(debt_id)
            if not self.has_debt_for_outbound(outbound_id):
                self.settle_outbound_order_and_items(outbound_id)
            messagebox.showinfo("提示", "欠款已全部结清！")
        else:
            self.update_debt_record(debt_id, new_debt)
            messagebox.showinfo("提示", f"结算成功，剩余欠款：{new_debt:.2f}")
        self.refresh()

    def update_outbound_payment_status(self, outbound_id):
        """同步更新出库单主表和明细表的已付/待付金额"""
        dbutil.update_outbound_payment_status(outbound_id)

    def ask_amount_and_method(self, max_debt):
        dialog = tk.Toplevel(self)
        dialog.title("结算欠款")
        dialog.grab_set()
        dialog.update_idletasks()
        w, h = 320, 140
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        tk.Label(dialog, text=f"本单剩余欠款：{max_debt}", font=("微软雅黑", 11)).pack(pady=(12, 2))
        frm = ttk.Frame(dialog)
        frm.pack(pady=6)
        tk.Label(frm, text="还款金额:", font=("微软雅黑", 11)).pack(side=tk.LEFT)
        amount_var = tk.StringVar(value=f"{max_debt:.2f}")
        amount_entry = ttk.Entry(frm, textvariable=amount_var, width=10)
        amount_entry.pack(side=tk.LEFT, padx=6)
        tk.Label(frm, text="支付方式:", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=(10,0))
        method_var = tk.StringVar(value="现金")
        method_combo = ttk.Combobox(frm, textvariable=method_var, values=["现金", "微信", "支付宝", "银联", "云闪付", "其他"], width=8, state="readonly")
        method_combo.pack(side=tk.LEFT, padx=4)
        result = {'amount': None, 'method': None}
        def on_ok():
            try:
                val = float(amount_var.get())
                if val < 0.01 or val > max_debt:
                    raise ValueError
            except Exception:
                messagebox.showwarning("提示", f"请输入0.01~{max_debt}之间的金额！", parent=dialog)
                return
            result['amount'] = float(amount_var.get())
            result['method'] = method_var.get()
            dialog.destroy()
        ttk.Button(dialog, text="确定", command=on_ok).pack(pady=8)
        amount_entry.focus_set()
        dialog.wait_window()
        return result['amount'], result['method']

    def has_debt_for_outbound(self, outbound_id):
        # 检查该出库单是否还有未结清的欠账
        debts = dbutil.get_all_debt_records()
        for d in debts:
            if str(d[1]) == str(outbound_id) and float(d[3]) > 0.01:
                return True
        return False

    def settle_outbound_order_and_items(self, outbound_id):
        # 结清主表和明细表
        conn = dbutil.sqlite3.connect(dbutil.DB_PATH)
        cursor = conn.cursor()
        # 获取主表合计金额
        cursor.execute("SELECT total_amount FROM outbound_order WHERE outbound_id=?", (outbound_id,))
        row = cursor.fetchone()
        if row:
            total_amount = float(row[0])
            # 更新主表
            cursor.execute("UPDATE outbound_order SET pay_status=2, total_paid=?, total_debt=0 WHERE outbound_id=?", (total_amount, outbound_id))
            # 更新明细表
            cursor.execute("UPDATE outbound_item SET item_pay_status=1, paid_amount=amount, debt_amount=0 WHERE outbound_id=?", (outbound_id,))
        conn.commit()
        conn.close()

    def update_debt_record(self, debt_id, new_debt):
        conn = dbutil.sqlite3.connect(dbutil.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE debt_record SET remaining_debt=? WHERE debt_id=?", (new_debt, debt_id))
        conn.commit()
        conn.close()

    def delete_debt_record(self, debt_id):
        conn = dbutil.sqlite3.connect(dbutil.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM debt_record WHERE debt_id=?", (debt_id,))
        conn.commit()
        conn.close()

    def export_statement_pdf(self):
        # 获取所有欠款记录
        debts = dbutil.get_all_debt_records()
        if not debts:
            messagebox.showinfo("提示", "没有欠款记录可导出！")
            return

        # 按客户分组统计
        customer_data = {}
        for debt in debts:
            debt_id, outbound_id, item_ids, remaining_debt = debt
            order = dbutil.get_outbound_order_by_id(outbound_id)
            if not order:
                continue
            order_no = order[1]
            customer_id = order[2]
            # 获取出库日期并只取前10个字符（日期部分）
            outbound_date = order[7][:10]
            customer = dbutil.get_customer_by_id(customer_id)
            if not customer:
                continue
            customer_name = customer[1]
            total_amount = order[3]
            # 处理可能的非数值total_paid
            try:
                total_paid = float(order[5])
            except (ValueError, TypeError):
                total_paid = 0.0

            # 获取订单明细
            outbound_items = dbutil.get_outbound_items_by_order(outbound_id)
            item_details = []
            for item in outbound_items:
                item_id, outbound_id, product_id, quantity, price, amount = item
                inventory = dbutil.get_inventory_by_id(product_id)
                if inventory:
                    factory, product_no, size, color, unit, _ = inventory[1:]
                    subtotal = float(quantity) * float(price)
                    # 添加出库日期到明细
                    item_details.append([order_no, outbound_date, product_no, color, unit, size, quantity, price, f"{subtotal:.2f}"])

            # 按客户分组
            if customer_name not in customer_data:
                customer_data[customer_name] = {
                    'total_amount': 0.0,
                    'total_paid': 0.0,
                    'remaining_debt': 0.0,
                    'orders': []
                }
            # 处理可能的非数值total_amount
            try:
                customer_data[customer_name]['total_amount'] += float(total_amount)
            except (ValueError, TypeError):
                customer_data[customer_name]['total_amount'] += 0.0
            customer_data[customer_name]['total_paid'] += float(total_paid)
            # 处理可能的非数值remaining_debt
            try:
                customer_data[customer_name]['remaining_debt'] += float(remaining_debt)
            except (ValueError, TypeError):
                customer_data[customer_name]['remaining_debt'] += 0.0
            customer_data[customer_name]['orders'].extend(item_details)

        # 使用PDFUtil工具类生成对账单
        if PDFUtil.create_customer_statement_pdf(customer_data):
            messagebox.showinfo("成功", "对账单已成功导出！")
