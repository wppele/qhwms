import tkinter as tk
from tkinter import ttk
from util import dbutil

class PaymentRecordPage(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        ttk.Label(self, text="付款记录查询", font=("微软雅黑", 16, "bold"), foreground="#2a5d2a").pack(pady=(18, 8))
        columns = ("payment_id", "outbound_id", "item_ids", "payment_amount", "pay_time", "pay_method")
        tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        for col, txt in zip(columns, ["记录ID", "出库单ID", "明细ID", "付款金额", "付款时间", "支付方式"]):
            tree.heading(col, text=txt)
            tree.column(col, anchor=tk.CENTER, width=120)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree = tree
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in dbutil.get_all_payment_records():
            # 兼容老数据，若无支付方式则补空
            if len(r) == 6:
                self.tree.insert('', tk.END, values=r)
            else:
                self.tree.insert('', tk.END, values=(*r, ""))
