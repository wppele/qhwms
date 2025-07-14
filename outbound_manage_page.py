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
    # 批量结账按钮
    def on_batch_payment():
        # 获取当前选中的订单（主表）
        sel = tree.selection()
        if not sel:
            tk.messagebox.showwarning("提示", "请先选择要结账的订单主行！")
            return
        # 找到选中行对应的 order_no
        order_no = tree.item(sel[0])['values'][0]
        if not order_no:
            tk.messagebox.showwarning("提示", "请在订单主行点击结账！")
            return
        # 获取主表信息
        all_rows = dbutil.get_all_outbound_orders()
        outbound_id = None
        for r in all_rows:
            if r[1] == order_no:
                outbound_id = r[0]
                break
        if not outbound_id:
            tk.messagebox.showerror("错误", "未找到对应出库单！")
            return
        # 获取明细
        items = dbutil.get_outbound_items_by_order(outbound_id)
        # items: (item_id, outbound_id, product_id, product_no, color, size, quantity, amount, item_pay_status, paid_amount, debt_amount, returnable_qty)
        item_list = [(i[0], i[3], i[4], i[5], i[6], i[7], i[9], i[10]) for i in items]
        from payment_dialog import PaymentDialog
        PaymentDialog(frame, outbound_id, item_list)

    def load_data():
        for row in tree.get_children():
            tree.delete(row)
        all_rows = dbutil.get_all_outbound_orders()
        # 新结构：r = (outbound_id, order_no, customer_id, total_amount, pay_status, total_paid, total_debt, create_time)
        order_map = {}
        for r in all_rows:
            order_no = r[1]
            if order_no not in order_map:
                order_map[order_no] = {
                    "outbound_id": r[0],
                    "order_no": r[1],
                    "customer_id": r[2],
                    "total_amount": r[3],
                    "pay_status": r[4],
                    "total_paid": r[5],
                    "total_debt": r[6],
                    "create_time": r[7],
                    "details": []
                }
            # 明细需单独查
        # 获取客户id到客户名的映射
        customer_map = {c[0]: c[1] for c in dbutil.get_all_customers()}
        for o in order_map.values():
            # 关联客户名
            o["customer_name"] = customer_map.get(o["customer_id"], "")
            items = dbutil.get_outbound_items_by_order(o["outbound_id"])
            for item in items:
                # item: (item_id, outbound_id, product_id, product_no, color, size, quantity, amount, item_pay_status, paid_amount, debt_amount, returnable_qty)
                o["details"].append({
                    "product_no": item[3],
                    "color": item[4],
                    "quantity": item[6]
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
            # 用 create_time 代替 outbound_date，pay_status 代替 is_paid
            for d in o["details"]:
                tree.insert("", tk.END, values=(
                    o["order_no"] if first else "",
                    o["customer_name"] if first else "",
                    d["product_no"],
                    d["color"],
                    d["quantity"],
                    o["create_time"] if first else "",
                    ("全额支付" if o["pay_status"]==2 else ("部分支付" if o["pay_status"]==1 else "欠款")) if first else "",
                    "" if first else "",
                    "" if first else ""
                ))
                first = False
    # 结账按钮
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill=tk.X, padx=10, pady=4)
    ttk.Button(btn_frame, text="批量结账", command=on_batch_payment, width=12).pack(side=tk.LEFT)
    frame.refresh = load_data
    load_data()
    return frame
