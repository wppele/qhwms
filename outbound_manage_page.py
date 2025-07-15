import tkinter as tk
from tkinter import ttk
from util import dbutil

def OutboundManagePage(parent):
    from outbound_detail_dialog import show_outbound_detail
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
    # 精简表格，仅展示主表核心信息
    columns = ("order_no", "customer_name", "total_amount", "create_time", "pay_status", "total_paid", "total_debt")
    headers = [
        ("order_no", "订单号"),
        ("customer_name", "客户"),
        ("total_amount", "合计金额"),
        ("create_time", "出库日期"),
        ("pay_status", "付款状态"),
        ("total_paid", "已付金额"),
        ("total_debt", "欠款")
    ]
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=120)

    def on_row_double_click(event):
        item = tree.identify_row(event.y)
        if not item:
            return
        vals = tree.item(item)['values']
        order_no = vals[0]
        if order_no:
            show_outbound_detail(frame, order_no)
    tree.bind('<Double-1>', on_row_double_click)

    def load_data():
        for row in tree.get_children():
            tree.delete(row)
        all_rows = dbutil.get_all_outbound_orders()
        customer_map = {c[0]: c[1] for c in dbutil.get_all_customers()}
        order_no_kw = search_order_no.get().strip()
        customer_kw = search_customer.get().strip()
        for r in all_rows:
            # r = (outbound_id, order_no, customer_id, total_amount, pay_status, total_paid, total_debt, create_time)
            order_no = r[1]
            customer_name = customer_map.get(r[2], "")
            if order_no_kw and order_no_kw not in order_no:
                continue
            if customer_kw and customer_kw not in customer_name:
                continue
            pay_status_str = "全额支付" if r[4]==2 else ("部分支付" if r[4]==1 else "欠款")
            tree.insert("", tk.END, values=(
                order_no,
                customer_name,
                f"{r[3]:.2f}",
                r[7],
                pay_status_str,
                f"{r[5]:.2f}",
                f"{r[6]:.2f}"
            ))
    frame.refresh = load_data
    load_data()
    return frame
