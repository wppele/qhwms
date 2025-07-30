import tkinter as tk
from tkinter import ttk, messagebox
from util import dbutil
import datetime

def PaymentDialog(parent, outbound_id, items):
    """
    批量结账弹窗
    :param parent: 父窗口
    :param outbound_id: 出库单主表ID
    :param items: [(item_id, product_no, color, quantity, amount, paid_amount, debt_amount), ...]
    """
    dialog = tk.Toplevel(parent)
    dialog.title("批量结账")
    w, h = 520, 420
    sw = dialog.winfo_screenwidth()
    sh = dialog.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    dialog.geometry(f"{w}x{h}+{x}+{y}")
    dialog.transient(parent)
    dialog.grab_set()
    ttk.Label(dialog, text="批量结账", font=("微软雅黑", 15, "bold"), foreground="#2a5d2a").pack(pady=(18, 8))
    # 结账明细表
    columns = ("sel", "product_no", "color", "quantity", "amount", "paid_amount", "debt_amount")
    headers = [
        ("sel", "选择"),
        ("product_no", "货号"),
        ("color", "颜色"),
        ("quantity", "数量"),
        ("amount", "金额"),
        ("paid_amount", "已付"),
        ("debt_amount", "欠款")
    ]
    tree = ttk.Treeview(dialog, columns=columns, show="headings", height=10)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    for col, text in headers:
        tree.heading(col, text=text)
        tree.column(col, anchor=tk.CENTER, width=70)
    # 填充明细，items: [(item_id, product_id, quantity, amount, paid_amount, debt_amount)]
    for item in items:
        item_id = item[0]
        inv = dbutil.get_inventory_by_id(item[1])
        product_no = inv[2] if inv else ''
        color = inv[4] if inv else ''
        quantity = item[2]
        amount = item[3]
        paid_amount = item[4]
        debt_amount = item[5]
        tree.insert("", tk.END, values=("", product_no, color, quantity, f"{amount:.2f}", f"{paid_amount:.2f}", f"{debt_amount:.2f}"), tags=(str(item_id),))
    # 选择框逻辑
    selected_items = set()
    def on_row_click(event):
        row = tree.identify_row(event.y)
        if not row:
            return
        item_id = int(tree.item(row)['tags'][0])
        if item_id in selected_items:
            selected_items.remove(item_id)
            tree.set(row, "sel", "")
        else:
            selected_items.add(item_id)
            tree.set(row, "sel", "✔")
    tree.bind('<Button-1>', on_row_click)
    # 支付金额输入
    pay_frame = ttk.Frame(dialog)
    pay_frame.pack(pady=8)
    ttk.Label(pay_frame, text="本次支付金额:", font=("微软雅黑", 11)).pack(side=tk.LEFT)
    pay_amount_var = tk.StringVar()
    ttk.Entry(pay_frame, textvariable=pay_amount_var, width=14).pack(side=tk.LEFT, padx=6)
    # 确认按钮
    def on_submit():
        try:
            pay_amount = float(pay_amount_var.get())
            if pay_amount <= 0:
                messagebox.showwarning("提示", "请输入大于0的支付金额！")
                return
            if not selected_items:
                messagebox.showwarning("提示", "请选择要结账的商品明细！")
                return
            # 获取选中明细，按欠款从小到大排序
            selected = []
            for item in items:
                if item[0] in selected_items:
                    selected.append(item)
            selected.sort(key=lambda x: x[7])  # 按欠款升序
            remain = pay_amount
            paid_ids = []
            pay_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for item in selected:
                item_id, _, _, _, _, amount, paid_amount, debt_amount = item
                if debt_amount <= 0:
                    continue
                if remain <= 0:
                    break
                pay_this = min(remain, debt_amount)
                # 更新明细表
                conn = dbutil.sqlite3.connect(dbutil.DB_PATH)
                cursor = conn.cursor()
                cursor.execute('UPDATE outbound_item SET paid_amount = paid_amount + ?, debt_amount = debt_amount - ?, item_pay_status = CASE WHEN debt_amount-?<=0 THEN 1 ELSE 0 END WHERE item_id=?',
                               (pay_this, pay_this, pay_this, item_id))
                conn.commit()
                conn.close()
                paid_ids.append(str(item_id))
                remain -= pay_this
            # 写入支付记录
            if paid_ids:
                dbutil.insert_payment_record(outbound_id, ','.join(paid_ids), pay_amount-remain, pay_time)
            # 统计所有明细的已付/欠款，更新主表
            conn = dbutil.sqlite3.connect(dbutil.DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(paid_amount), SUM(debt_amount) FROM outbound_item WHERE outbound_id=?', (outbound_id,))
            row = cursor.fetchone()
            total_paid = row[0] if row[0] else 0
            total_debt = row[1] if row[1] else 0
            if total_debt <= 0:
                pay_status = 2  # 全额
            elif total_paid > 0:
                pay_status = 1  # 部分
            else:
                pay_status = 0  # 未支付
            cursor.execute('UPDATE outbound_order SET total_paid=?, total_debt=?, pay_status=? WHERE outbound_id=?',
                           (total_paid, total_debt, pay_status, outbound_id))
            conn.commit()
            conn.close()
            if hasattr(parent, 'refresh') and callable(parent.refresh):
                parent.refresh()
            messagebox.showinfo("成功", f"支付成功，实际支付：{pay_amount-remain:.2f} 元")
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"结账失败：{e}")
    ttk.Button(dialog, text="确认结账", command=on_submit, width=14).pack(pady=12)
    dialog.wait_window()
