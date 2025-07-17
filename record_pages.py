import tkinter as tk
from tkinter import ttk
from util import dbutil

def SettleLogPage(parent):
    frame = ttk.Frame(parent)
    columns = ("factory", "product_no", "color", "in_quantity", "price", "total", "settle_date")
    headers = [
        ("factory", "厂家"),
        ("product_no", "货号"),
        ("color", "颜色"),
        ("in_quantity", "入库数量"),
        ("price", "单价"),
        ("total", "合计"),
        ("settle_date", "结账日期")
    ]
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=90)
    def load_data():
        for row in tree.get_children():
            tree.delete(row)
        for row in dbutil.get_all_settle_log():
            tree.insert("", tk.END, values=row)
    frame.refresh = load_data
    load_data()
    return frame

def StockLogPage(parent):
    frame = ttk.Frame(parent)
    columns = ("factory", "product_no", "size", "color", "in_quantity", "action_type", "action_date")
    headers = [
        ("factory", "厂家"),
        ("product_no", "货号"),
        ("size", "尺码"),
        ("color", "颜色"),
        ("in_quantity", "入库数量"),
        ("action_type", "类型"),
        ("action_date", "日期")
    ]
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=90)
    def load_data():
        for row in tree.get_children():
            tree.delete(row)
        for row in dbutil.get_all_stock_log():
            # row: factory, product_no, size, color, in_quantity, action_type, action_date
            tree.insert("", tk.END, values=row)
    frame.refresh = load_data
    load_data()
    return frame
