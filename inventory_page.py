import tkinter as tk
from tkinter import ttk
from util import dbutil

def InventoryPage(parent):
    frame = ttk.Frame(parent)
    columns = ("id", "stock_id", "factory", "product_no", "size", "color", "quantity")
    headers = [
        ("id", "序号"),
        ("stock_id", "入库ID"),
        ("factory", "厂家"),
        ("product_no", "货号"),
        ("size", "尺码"),
        ("color", "颜色"),
        ("quantity", "库存数量")
    ]
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=90)
    def load_data():
        for row in tree.get_children():
            tree.delete(row)
        for row in dbutil.get_all_inventory():
            tree.insert("", tk.END, values=row)
    frame.refresh = load_data
    load_data()
    return frame
