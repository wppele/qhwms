import tkinter as tk
from tkinter import ttk
from util import dbutil

class PaymentRecordPage(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        ttk.Label(self, text="付款记录查询", font=("微软雅黑", 16, "bold"), foreground="#2a5d2a").pack(pady=(18, 8))
        columns = ("no", "order_no", "customer", "payment_amount", "pay_time", "pay_method")
        tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        for col, txt in zip(columns, ["序号", "订单号", "客户", "付款金额", "付款时间", "支付方式"]):
            tree.heading(col, text=txt)
            tree.column(col, anchor=tk.CENTER, width=120)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree = tree
        self.tree.bind('<Double-1>', self.on_double_click)
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        all_records = dbutil.get_all_payment_records()
        # 获取订单号和客户名映射
        order_map = {}
        customer_map = {}
        for order in dbutil.get_all_outbound_orders():
            # order: (outbound_id, order_no, customer_id, ...)
            order_map[order[0]] = order[1]
            customer_map[order[0]] = order[2]
        customer_name_map = {}
        for c in dbutil.get_all_customers():
            # c: (id, name, ...)
            customer_name_map[c[0]] = c[1]
        for idx, r in enumerate(all_records, 1):
            outbound_id = r[1]
            order_no = order_map.get(outbound_id, outbound_id)
            customer_id = customer_map.get(outbound_id, None)
            customer = customer_name_map.get(customer_id, "")
            payment_amount = r[3]
            pay_time = r[4]
            pay_method = r[5] if len(r) > 5 else ""
            self.tree.insert('', tk.END, values=(idx, order_no, customer, payment_amount, pay_time, pay_method))

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        vals = self.tree.item(item, 'values')
        order_no = vals[1]
        # 查找对应outbound_id
        outbound_id = None
        for order in dbutil.get_all_outbound_orders():
            if order[1] == order_no:
                outbound_id = order[0]
                break
        if not outbound_id:
            tk.messagebox.showinfo("订单明细", "未找到该订单明细。")
            return
        details = dbutil.get_outbound_items_by_order(outbound_id)
        if not details:
            tk.messagebox.showinfo("订单明细", "未找到该订单明细。")
            return
        detail_win = tk.Toplevel(self)
        detail_win.title(f"订单明细 - 订单号：{order_no}")
        columns = ("product_no", "size", "color", "quantity", "amount", "item_pay_status", "paid_amount", "debt_amount")
        headers = ["货号", "尺码", "颜色", "数量", "金额", "支付状态", "已付", "待付"]
        tree = ttk.Treeview(detail_win, columns=columns, show="headings", height=10)
        for col, txt in zip(columns, headers):
            tree.heading(col, text=txt)
            tree.column(col, anchor=tk.CENTER, width=90)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for row in details:
            # row: item_id, outbound_id, product_id, quantity, amount, item_pay_status, paid_amount, debt_amount, returnable_qty
            inv = dbutil.get_inventory_by_id(row[2])
            product_no = inv[2] if inv else ''
            size = inv[4] if inv else ''
            color = inv[5] if inv else ''
            tree.insert('', tk.END, values=(product_no, size, color, row[3], row[4], row[5], row[6], row[7]))
        ttk.Button(detail_win, text="关闭", command=detail_win.destroy).pack(pady=8)
