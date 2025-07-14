import tkinter as tk
from tkinter import ttk
from util import dbutil

def OutboundManagePage(parent):
    frame = ttk.Frame(parent)
    # 标题
    ttk.Label(frame, text="出库单管理", font=("微软雅黑", 16, "bold"), foreground="#2a5d2a").pack(pady=(18, 8))
    # 搜索栏
    search_frame = ttk.Frame(frame)
    search_frame.pack(fill=tk.X, padx=10, pady=8)
    ttk.Label(search_frame, text="订单号:").pack(side=tk.LEFT)
    search_order_no = tk.StringVar()
    ttk.Entry(search_frame, textvariable=search_order_no, width=16).pack(side=tk.LEFT, padx=4)
    ttk.Label(search_frame, text="客户:").pack(side=tk.LEFT)
    search_customer = tk.StringVar()
    ttk.Entry(search_frame, textvariable=search_customer, width=14).pack(side=tk.LEFT, padx=4)
    def do_search():
        load_data()
    ttk.Button(search_frame, text="搜索", command=do_search, width=8).pack(side=tk.LEFT, padx=8)
    # 表格区
    columns = ("order_no", "customer_name", "product_no", "color", "quantity", "outbound_date", "is_paid", "pay_method", "pay_date")
    headers = [
        ("order_no", "订单号"),
        ("customer_name", "客户"),
        ("product_no", "货号"),
        ("color", "颜色"),
        ("quantity", "数量"),
        ("outbound_date", "出库日期"),
        ("is_paid", "付款状态"),
        ("pay_method", "付款方式"),
        ("pay_date", "付款日期")
    ]
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=110)
    # 加载数据
    def load_data():
        for row in tree.get_children():
            tree.delete(row)
        all_rows = dbutil.get_all_outbound_orders()
        # 合并相同订单号，订单下多行明细
        order_map = {}
        for r in all_rows:
            # r: (id, order_no, customer_name, address, logistics_info, product_no, color, size, quantity, price, total, outbound_date, is_paid, pay_method, pay_date)
            order_no = r[1]
            if order_no not in order_map:
                order_map[order_no] = {
                    "order_no": r[1],
                    "customer_name": r[2],
                    "outbound_date": r[11],
                    "is_paid": r[12],
                    "pay_method": r[13],
                    "pay_date": r[14],
                    "details": []
                }
            order_map[order_no]["details"].append({
                "product_no": r[5],
                "color": r[6],
                "quantity": r[8]
            })
        # 搜索过滤
        order_list = list(order_map.values())
        order_no_kw = search_order_no.get().strip()
        customer_kw = search_customer.get().strip()
        if order_no_kw:
            order_list = [o for o in order_list if order_no_kw in o["order_no"]]
        if customer_kw:
            order_list = [o for o in order_list if customer_kw in (o["customer_name"] or "")]
        # 展示：每个订单一行主信息，明细多行
        for o in order_list:
            first = True
            for d in o["details"]:
                tree.insert("", tk.END, values=(
                    o["order_no"] if first else "",
                    o["customer_name"] if first else "",
                    d["product_no"],
                    d["color"],
                    d["quantity"],
                    o["outbound_date"] if first else "",
                    ("已付款" if o["is_paid"] else "欠款") if first else "",
                    o["pay_method"] if first else "",
                    o["pay_date"] if first else ""
                ))
                first = False
    frame.refresh = load_data
    load_data()
    return frame
