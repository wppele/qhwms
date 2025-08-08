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
        ttk.Button(filter_frame, text="生成对账单", command=self.generate_statement, width=10).pack(side=tk.LEFT, padx=8)
        ttk.Button(filter_frame, text="批量结算", command=self.batch_settle, width=10).pack(side=tk.LEFT, padx=8)

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
        # 结清主表
        conn = dbutil.sqlite3.connect(dbutil.DB_PATH)
        cursor = conn.cursor()
        # 获取主表合计金额
        cursor.execute("SELECT total_amount FROM outbound_order WHERE outbound_id=?", (outbound_id,))
        row = cursor.fetchone()
        if row:
            total_amount = float(row[0])
            # 更新主表
            cursor.execute("UPDATE outbound_order SET pay_status=2, total_paid=?, total_debt=0 WHERE outbound_id=?", (total_amount, outbound_id))
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

    def batch_settle(self):
        """批量结算功能"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请选择需要结账的条目！")
            return

        # 检查是否是同一个客户
        customer_names = set()
        total_debt = 0.0
        selected_data = []

        for item in selected_items:
            values = self.tree.item(item, "values")
            customer_name = values[2]
            customer_names.add(customer_name)
            remaining_debt = float(values[5])
            total_debt += remaining_debt

            # 获取tag信息
            tag = self.tree.item(item).get('tags', ('',))[0]
            try:
                debt_id, outbound_id, item_ids = tag.split('|', 2)
                selected_data.append({
                    'debt_id': debt_id,
                    'outbound_id': outbound_id,
                    'item_ids': item_ids,
                    'remaining_debt': remaining_debt,
                    'order_no': values[1],
                    'total_amount': float(values[3]),
                    'total_paid': float(values[4])
                })
            except Exception:
                messagebox.showerror("错误", "无法获取欠账记录ID")
                return

        if len(customer_names) > 1:
            messagebox.showinfo("提示", "不能对多个客户同时结账！")
            return

        customer_name = list(customer_names)[0]

        # 弹出对话框显示总欠款金额，让用户输入还款金额和支付方式
        pay_amount, pay_method = self.ask_batch_amount_and_method(total_debt, customer_name)
        if pay_amount is None or not pay_method:
            return

        # 按欠款金额从小到大排序，优先结清小额欠款
        selected_data.sort(key=lambda x: x['remaining_debt'])

        remain = pay_amount
        paid_records = []
        from datetime import datetime
        pay_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for data in selected_data:
            if remain <= 0:
                break

            debt_id = data['debt_id']
            outbound_id = data['outbound_id']
            item_ids = data['item_ids']
            remaining_debt = data['remaining_debt']

            pay_this = min(remain, remaining_debt)
            paid_records.append({
                'outbound_id': outbound_id,
                'item_ids': item_ids,
                'pay_amount': pay_this,
                'order_no': data['order_no']
            })

            # 写入payment_record，支付方式格式：支付方式-批量支付金额
            payment_method = f"{pay_method}-批量支付金额:{pay_amount:.2f}"

            dbutil.insert_payment_record(outbound_id, item_ids, pay_this, pay_time, payment_method)

            # 更新debt_record
            new_debt = remaining_debt - pay_this
            if new_debt <= 0.01:
                self.delete_debt_record(debt_id)
                if not self.has_debt_for_outbound(outbound_id):
                    self.settle_outbound_order_and_items(outbound_id)
            else:
                self.update_debt_record(debt_id, new_debt)

            # 同步更新出库单主表和明细表的已付/待付金额
            self.update_outbound_payment_status(outbound_id)

            remain -= pay_this

        # 显示结算结果
        if remain <= 0.01:
            messagebox.showinfo("提示", f"结算成功，全部欠款已结清！总支付金额：{pay_amount:.2f}")
        else:
            messagebox.showinfo("提示", f"结算成功，部分欠款已结清！已支付：{pay_amount-remain:.2f}，剩余：{remain:.2f}")

        self.refresh()

    def ask_batch_amount_and_method(self, total_debt, customer_name):
        """批量结算时询问还款金额和支付方式"""
        dialog = tk.Toplevel(self)
        dialog.title("批量结算")
        dialog.grab_set()
        dialog.update_idletasks()
        w, h = 360, 180
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(dialog, text=f"客户：{customer_name}", font=("微软雅黑", 11)).pack(pady=(10, 2))
        tk.Label(dialog, text=f"总欠款金额：{total_debt:.2f}", font=("微软雅黑", 11)).pack(pady=(2, 8))

        frm = ttk.Frame(dialog)
        frm.pack(pady=6)

        tk.Label(frm, text="还款金额:", font=("微软雅黑", 11)).pack(side=tk.LEFT)
        amount_var = tk.StringVar(value=f"{total_debt:.2f}")
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
                if val < 0.01 or val > total_debt:
                    raise ValueError
            except Exception:
                messagebox.showwarning("提示", f"请输入0.01~{total_debt:.2f}之间的金额！", parent=dialog)
                return
            result['amount'] = float(amount_var.get())
            result['method'] = method_var.get()
            dialog.destroy()

        btn_frm = ttk.Frame(dialog)
        btn_frm.pack(pady=12)
        ttk.Button(btn_frm, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frm, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

        amount_entry.focus_set()
        dialog.wait_window()
        return result['amount'], result['method']

    def generate_statement(self):
        """生成对账单"""
        # 创建日期选择对话框
        dialog = tk.Toplevel(self)
        dialog.title("选择对账单周期")
        dialog.grab_set()
        dialog.update_idletasks()
        w, h = 360, 180
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        
        ttk.Label(dialog, text="请选择对账单周期:", font=("微软雅黑", 11)).pack(pady=(12, 8))
        
        # 开始日期
        frm_start = ttk.Frame(dialog)
        frm_start.pack(pady=4, fill=tk.X, padx=20)
        ttk.Label(frm_start, text="开始日期:", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        start_date_var = tk.StringVar()
        if has_tkcalendar:
            start_date_entry = DateEntry(frm_start, textvariable=start_date_var, width=12, date_pattern='yyyy-mm-dd')
            start_date_entry.pack(side=tk.LEFT, padx=4)
        else:
            ttk.Entry(frm_start, textvariable=start_date_var, width=14).pack(side=tk.LEFT, padx=4)
            ttk.Label(frm_start, text="(格式: yyyy-mm-dd)", font=('Arial', 8)).pack(side=tk.LEFT)
        
        # 结束日期
        frm_end = ttk.Frame(dialog)
        frm_end.pack(pady=4, fill=tk.X, padx=20)
        ttk.Label(frm_end, text="结束日期:", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        end_date_var = tk.StringVar()
        if has_tkcalendar:
            end_date_entry = DateEntry(frm_end, textvariable=end_date_var, width=12, date_pattern='yyyy-mm-dd')
            end_date_entry.pack(side=tk.LEFT, padx=4)
        else:
            ttk.Entry(frm_end, textvariable=end_date_var, width=14).pack(side=tk.LEFT, padx=4)
            ttk.Label(frm_end, text="(格式: yyyy-mm-dd)", font=('Arial', 8)).pack(side=tk.LEFT)
        
        result = {'start_date': None, 'end_date': None}
        
        def on_ok():
            start_date = start_date_var.get().strip()
            end_date = end_date_var.get().strip()
            
            if not start_date or not end_date:
                messagebox.showwarning("提示", "请选择开始日期和结束日期！", parent=dialog)
                return
            
            # 验证日期格式
            try:
                from datetime import datetime
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                messagebox.showwarning("提示", "日期格式不正确，请使用yyyy-mm-dd格式！", parent=dialog)
                return
            
            result['start_date'] = start_date
            result['end_date'] = end_date
            dialog.destroy()
        
        btn_frm = ttk.Frame(dialog)
        btn_frm.pack(pady=12)
        ttk.Button(btn_frm, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frm, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
        dialog.wait_window()
        
        if result['start_date'] and result['end_date']:
            # 按客户分组生成对账单
            self.create_statements_by_customer(result['start_date'], result['end_date'])

    def create_statements_by_customer(self, start_date, end_date):
        """按客户生成对账单"""
        conn = dbutil.sqlite3.connect(dbutil.DB_PATH)
        cursor = conn.cursor()
        
        try:
            # 获取所有未结清的订单(pay_status != 2)
            cursor.execute("""
                SELECT o.outbound_id, o.customer_id, o.order_no, o.total_amount, o.total_paid, o.total_debt, o.create_time
                FROM outbound_order o
                WHERE o.pay_status != 2
            """)
            orders = cursor.fetchall()
            
            # 按客户分组
            customer_orders = {}
            for order in orders:
                outbound_id, customer_id, order_no, total_amount, total_paid, total_debt, create_time = order
                
                # 获取客户名称
                cursor.execute("SELECT name FROM customer_info WHERE id=?", (customer_id,))
                customer = cursor.fetchone()
                if not customer:
                    continue
                customer_name = customer[0]
                
                # 格式化日期
                outbound_date = create_time.split(' ')[0] if create_time else ''
                
                if customer_name not in customer_orders:
                    customer_orders[customer_name] = {
                        'customer_id': customer_id,
                        'orders': [],
                        'previous_debt': 0.0,
                        'current_debt': 0.0
                    }
                
                # 判断订单日期是否在选择区间内
                if outbound_date and outbound_date >= start_date and outbound_date <= end_date:
                    # 当前区间内的订单
                    customer_orders[customer_name]['current_debt'] += float(total_debt)
                    customer_orders[customer_name]['orders'].append(outbound_id)
                elif outbound_date and outbound_date < start_date:
                    # 区间之前的订单
                    customer_orders[customer_name]['previous_debt'] += float(total_debt)
                    customer_orders[customer_name]['orders'].append(outbound_id)
            
            # 生成对账单
            from datetime import datetime
            current_date = datetime.now().strftime("%Y-%m-%d")
            bill_period = f"{start_date} 至 {end_date}"
            
            for customer_name, data in customer_orders.items():
                # 跳过没有订单的客户
                if not data['orders']:
                    continue
                
                # 生成对账单号
                # 生成对账单号: DZ+年月日+第几个对账单
                statement_no = f"DZ{current_date.replace('-', '')}{len(data['orders'])}"
                
                # 计算总金额
                total_amount = data['previous_debt'] + data['current_debt']
                
                # 存储订单ID，用逗号分隔
                outbound_ids = ','.join(map(str, data['orders']))
                
                # 插入对账单记录
                cursor.execute("""
                    INSERT INTO statement (
                        statement_no, customer_name, outbound_ids, previous_debt, 
                        current_debt, total_amount, bill_period, issue_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    statement_no, customer_name, outbound_ids, data['previous_debt'],
                    data['current_debt'], total_amount, bill_period, current_date
                ))
            
            conn.commit()
            messagebox.showinfo("成功", f"对账单已生成，共 {len(customer_orders)} 份！")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("错误", f"生成对账单失败：{str(e)}")
        finally:
            conn.close()
