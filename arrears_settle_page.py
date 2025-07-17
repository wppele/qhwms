import tkinter as tk
from tkinter import ttk, messagebox
from util import dbutil

class ArrearsSettlePage(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()
        self.refresh()

    def create_widgets(self):
        # 新表头：序号、客户姓名、订单号、剩余欠款
        columns = ("serial", "customer_name", "order_no", "remaining_debt")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("serial", text="序号")
        self.tree.heading("customer_name", text="客户")
        self.tree.heading("order_no", text="订单号")
        self.tree.heading("remaining_debt", text="剩余欠款")
        self.tree.column("serial", width=60, anchor=tk.CENTER)
        self.tree.column("customer_name", width=120, anchor=tk.CENTER)
        self.tree.column("order_no", width=140, anchor=tk.CENTER)
        self.tree.column("remaining_debt", width=100, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)
        settle_btn = ttk.Button(btn_frame, text="结算选中欠款", command=self.settle_selected)
        settle_btn.pack(side=tk.LEFT, padx=10)
        refresh_btn = ttk.Button(btn_frame, text="刷新", command=self.refresh)
        refresh_btn.pack(side=tk.LEFT)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        debts = dbutil.get_all_debt_records()
        # debts: (debt_id, outbound_id, item_ids, remaining_debt)
        # 需要查客户姓名和订单号
        for idx, debt in enumerate(debts, 1):
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
            self.tree.insert('', tk.END, values=(idx, customer_name, order_no, f"{remaining_debt:.2f}"), tags=(f"{debt_id}|{outbound_id}|{item_ids}",))

    def settle_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一条欠账记录！")
            return
        item = self.tree.item(selected[0])
        # 通过tag获取真实debt_id, outbound_id, item_ids
        tag = self.tree.item(selected[0]).get('tags', ('',))[0]
        try:
            debt_id, outbound_id, item_ids = tag.split('|', 2)
        except Exception:
            messagebox.showerror("错误", "无法获取欠账记录ID")
            return
        remaining_debt = float(item['values'][3])
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
        # 汇总所有payment_record的payment_amount
        import sqlite3
        conn = sqlite3.connect(dbutil.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(payment_amount) FROM payment_record WHERE outbound_id=?", (outbound_id,))
        paid = cursor.fetchone()[0] or 0.0
        # 获取主表总金额
        cursor.execute("SELECT total_amount FROM outbound_order WHERE outbound_id=?", (outbound_id,))
        total = cursor.fetchone()[0] or 0.0
        debt = total - paid
        # 更新主表
        pay_status = 2 if debt <= 0.01 else (1 if paid > 0 else 0)
        cursor.execute("UPDATE outbound_order SET total_paid=?, total_debt=?, pay_status=? WHERE outbound_id=?", (paid, debt, pay_status, outbound_id))
        # 明细表全部同步为部分/全额已付
        cursor.execute("SELECT item_id, amount FROM outbound_item WHERE outbound_id=?", (outbound_id,))
        items = cursor.fetchall()
        # 按比例分配已付金额到明细
        remain_paid = paid
        for item_id, amount in items:
            if paid >= total and total > 0:
                paid_amt = amount
                debt_amt = 0.0
                item_pay_status = 1
            elif total > 0:
                ratio = amount / total
                paid_amt = round(paid * ratio, 2)
                debt_amt = amount - paid_amt
                item_pay_status = 1 if debt_amt <= 0.01 else 0
            else:
                paid_amt = 0.0
                debt_amt = amount
                item_pay_status = 0
            cursor.execute("UPDATE outbound_item SET paid_amount=?, debt_amount=?, item_pay_status=? WHERE item_id=?", (paid_amt, debt_amt, item_pay_status, item_id))
        conn.commit()
        conn.close()

    def ask_amount_and_method(self, max_debt):
        dialog = tk.Toplevel(self)
        dialog.title("结算欠款")
        dialog.grab_set()
        dialog.geometry("320x140")
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
