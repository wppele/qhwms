# 结算日志页面
import tkinter as tk
from tkinter import ttk
from util import dbutil

def SettleLogPage(parent):
    frame = ttk.Frame(parent)
    # 筛选区
    filter_frame = ttk.Frame(frame)
    filter_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
    ttk.Label(filter_frame, text="厂家:").pack(side=tk.LEFT)
    factory_var = tk.StringVar()
    factory_entry = ttk.Entry(filter_frame, textvariable=factory_var, width=12)
    factory_entry.pack(side=tk.LEFT, padx=4)
    ttk.Label(filter_frame, text="货号:").pack(side=tk.LEFT)
    product_var = tk.StringVar()
    product_entry = ttk.Entry(filter_frame, textvariable=product_var, width=12)
    product_entry.pack(side=tk.LEFT, padx=4)
    def on_filter():
        load_data()
    ttk.Button(filter_frame, text="筛选", command=on_filter).pack(side=tk.LEFT, padx=8)
    # 绑定回车键事件
    factory_entry.bind('<Return>', lambda e: on_filter())
    product_entry.bind('<Return>', lambda e: on_filter())

    columns = ("factory", "product_no", "size", "color", "in_quantity", "price", "total", "settle_date")
    headers = [
        ("factory", "厂家"),
        ("product_no", "货号"),
        ("size", "尺寸"),
        ("color", "颜色"),
        ("in_quantity", "数量"),
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
        factory = factory_var.get().strip()
        product_no = product_var.get().strip()
        for row in dbutil.get_all_settle_log():
            # row: factory, product_no, size, color, in_quantity, price, total, settle_date
            if (not factory or row[0] == factory) and (not product_no or row[1] == product_no):
                tree.insert("", tk.END, values=row)
    frame.refresh = load_data
    load_data()
    return frame

def StockLogPage(parent):
    frame = ttk.Frame(parent)
    # 筛选区
    filter_frame = ttk.Frame(frame)
    filter_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
    ttk.Label(filter_frame, text="厂家:").pack(side=tk.LEFT)
    factory_var = tk.StringVar()
    factory_entry = ttk.Entry(filter_frame, textvariable=factory_var, width=12)
    factory_entry.pack(side=tk.LEFT, padx=4)
    ttk.Label(filter_frame, text="货号:").pack(side=tk.LEFT)
    product_var = tk.StringVar()
    product_entry = ttk.Entry(filter_frame, textvariable=product_var, width=12)
    product_entry.pack(side=tk.LEFT, padx=4)
    def on_filter():
        load_data()
    ttk.Button(filter_frame, text="筛选", command=on_filter).pack(side=tk.LEFT, padx=8)

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
        factory = factory_var.get().strip()
        product_no = product_var.get().strip()
        for row in dbutil.get_all_stock_log():
            # row: factory, product_no, size, color, in_quantity, action_type, action_date
            if (not factory or row[0] == factory) and (not product_no or row[1] == product_no):
                tree.insert("", tk.END, values=row)
    frame.refresh = load_data
    load_data()
    return frame
