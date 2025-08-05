import tkinter as tk
from tkinter import ttk, messagebox
from util import dbutil

class SaleReturnPage(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()
        self.refresh()

    def create_widgets(self):
        # 筛选区
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(filter_frame, text="订单号:").pack(side=tk.LEFT)
        self.search_order_no = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.search_order_no, width=16).pack(side=tk.LEFT, padx=4)
        ttk.Label(filter_frame, text="货号:").pack(side=tk.LEFT)
        self.search_product_no = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.search_product_no, width=14).pack(side=tk.LEFT, padx=4)
        ttk.Button(filter_frame, text="筛选", command=self.refresh, width=8).pack(side=tk.LEFT, padx=8)

        columns = ("order_no", "item_id", "product_no", "color", "size", "quantity", "price", "amount", "return_qty")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("order_no", text="订单号")
        self.tree.heading("item_id", text="明细ID")
        self.tree.heading("product_no", text="货号")
        self.tree.heading("color", text="颜色")
        self.tree.heading("size", text="尺码")
        self.tree.heading("quantity", text="数量")
        self.tree.heading("price", text="单价")
        self.tree.heading("amount", text="金额")
        self.tree.heading("return_qty", text="可退数量")
        self.tree.column("order_no", width=130, anchor=tk.CENTER)
        self.tree.column("item_id", width=70, anchor=tk.CENTER)
        self.tree.column("product_no", width=100, anchor=tk.CENTER)
        self.tree.column("color", width=80, anchor=tk.CENTER)
        self.tree.column("size", width=70, anchor=tk.CENTER)
        self.tree.column("quantity", width=70, anchor=tk.CENTER)
        self.tree.column("price", width=70, anchor=tk.E)
        self.tree.column("amount", width=80, anchor=tk.E)
        self.tree.column("return_qty", width=80, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # 鼠标悬停表格项时显示提示
        def show_tooltip(event):
            widget = event.widget
            row_id = widget.identify_row(event.y)
            if row_id:
                if not hasattr(widget, '_tooltip_label'):
                    widget._tooltip_label = tk.Label(widget, text="双击退货", bg="#ffffe0", fg="#333", font=("微软雅黑", 10), relief=tk.SOLID, bd=1)
                widget._tooltip_label.place_forget()
                widget._tooltip_label.place(x=event.x, y=event.y+18)
            else:
                if hasattr(widget, '_tooltip_label'):
                    widget._tooltip_label.place_forget()
        def hide_tooltip(event):
            widget = event.widget
            if hasattr(widget, '_tooltip_label'):
                widget._tooltip_label.place_forget()
        self.tree.bind('<Motion>', show_tooltip)
        self.tree.bind('<Leave>', hide_tooltip)
        self.tree.bind('<Double-1>', self.on_double_click)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        order_no_kw = getattr(self, 'search_order_no', tk.StringVar()).get().strip() if hasattr(self, 'search_order_no') else ''
        product_no_kw = getattr(self, 'search_product_no', tk.StringVar()).get().strip() if hasattr(self, 'search_product_no') else ''
        orders = dbutil.get_all_outbound_orders()
        for order in orders:
            outbound_id, order_no = order[0], order[1]
            items = dbutil.get_outbound_items_by_order(outbound_id)
            for item in items:
                item_id, _, product_id, quantity, price, amount, *_ = item
                inv = dbutil.get_inventory_by_id(product_id)
                if inv:
                    product_no = inv[2]
                    color = inv[4]
                    size = inv[3]
                else:
                    product_no = color = size = ''
                # 获取可退数量（returnable_qty字段）
                try:
                    returnable_qty = item[9] if len(item) > 9 else quantity
                except Exception:
                    returnable_qty = quantity
                # 筛选逻辑
                if order_no_kw and order_no_kw not in str(order_no):
                    continue
                if product_no_kw and product_no_kw not in str(product_no):
                    continue
                if returnable_qty > 0:
                    self.tree.insert('', tk.END, values=(order_no, item_id, product_no, color, size, quantity, price, amount, returnable_qty))

    def on_double_click(self, event):
        item_id = None
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        vals = item['values']
        item_id = vals[1]
        product_no = vals[2]
        color = vals[3]
        size = vals[4]
        quantity = int(float(vals[5]))
        returnable_qty = int(float(vals[8]))
        # 弹窗输入退货数量（以可退数量为准）
        return_qty = self.ask_return_qty(returnable_qty)
        if return_qty is None or return_qty <= 0:
            return
        # 更新库存
        inv = dbutil.get_inventory_by_id_by_fields(product_no, color, size)
        if inv:
            dbutil.increase_inventory_by_id(inv[0], return_qty)
        else:
            messagebox.showerror("错误", "未找到对应库存，无法退货")
            return
        # 更新出库明细表的returnable_qty字段和quantity字段
        dbutil.decrease_returnable_qty_by_item_id(item_id, return_qty)
        dbutil.decrease_outbound_item_quantity(item_id, return_qty)
        # 同步更新该明细的总金额（amount=price*quantity）
        # 先查最新quantity
        order_no = vals[0]
        outbound_id = dbutil.get_outbound_id_by_order_no(order_no)
        item_row = None
        items = dbutil.get_outbound_items_by_order(outbound_id)
        for it in items:
            if str(it[0]) == str(item_id):
                item_row = it
                break
        if item_row:
            new_qty = float(item_row[3]) if item_row[3] else 0
            new_price = float(item_row[4]) if item_row[4] else 0
            new_amount = new_qty * new_price
            dbutil.update_outbound_item_amount(item_id, new_amount)
            # 数量为0则删除该明细
            if new_qty <= 0.01:
                dbutil.delete_outbound_item_by_id(item_id)
        # 新增退款记录到payment_record
        order_no = vals[0]
        outbound_id = dbutil.get_outbound_id_by_order_no(order_no)
        from datetime import datetime
        # 退款金额=退货数量*单价，单价为vals[6]
        try:
            price = float(vals[6])
        except Exception:
            price = 0.0
        refund_amount = -abs(return_qty * price)
        dbutil.insert_payment_record(
            outbound_id,
            str(item_id),
            refund_amount,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "退款"
        )
        # 同步修改出库单主表金额
        # 退货后重新统计该出库单所有明细的总金额
        items = dbutil.get_outbound_items_by_order(outbound_id)
        new_total_amount = 0.0
        for item in items:
            qty = float(item[3]) if item[3] else 0
            price = float(item[4]) if item[4] else 0
            new_total_amount += price * qty
        # 如果主表总金额为0，删除主表
        if new_total_amount <= 0.01:
            dbutil.delete_outbound_order_by_id(outbound_id)
            dbutil.delete_debt_record_by_outboundid(outbound_id)
            messagebox.showinfo("成功", f"退货成功，已将{product_no} {color} {size} 库存增加{return_qty}，明细和出库单及余款结算已全部删除")
            self.refresh()
            return
        order_row = dbutil.get_outbound_order_by_id(outbound_id)
        if order_row:
            total_paid = float(order_row[5]) if order_row[5] else 0.0
            new_total_debt = max(new_total_amount - total_paid, 0)
            new_total_paid = min(total_paid, new_total_amount)
            if new_total_debt <= 0.01:
                pay_status = 2
            elif new_total_paid > 0:
                pay_status = 1
            else:
                pay_status = 0
            dbutil.update_outbound_order_amount(outbound_id, new_total_amount, new_total_paid, new_total_debt, pay_status)
        messagebox.showinfo("成功", f"退货成功，已将{product_no} {color} {size} 库存增加{return_qty}，并生成退款记录")
        self.refresh()

    def ask_return_qty(self, max_qty):
        dialog = tk.Toplevel(self)
        dialog.title("退货数量")
        dialog.grab_set()
        dialog.update_idletasks()
        w, h = 260, 120
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        tk.Label(dialog, text=f"本单可退数量：{max_qty}", font=("微软雅黑", 11)).pack(pady=(12, 2))
        frm = ttk.Frame(dialog)
        frm.pack(pady=6)
        tk.Label(frm, text="退货数量:", font=("微软雅黑", 11)).pack(side=tk.LEFT)
        qty_var = tk.StringVar(value="1")
        qty_entry = ttk.Entry(frm, textvariable=qty_var, width=8)
        qty_entry.pack(side=tk.LEFT, padx=6)
        result = {'qty': None}
        def on_ok():
            try:
                val = int(qty_var.get())
                if val < 1 or val > max_qty:
                    raise ValueError
            except Exception:
                messagebox.showwarning("提示", f"请输入1~{max_qty}之间的整数！", parent=dialog)
                return
            result['qty'] = val
            dialog.destroy()
        btn = ttk.Button(dialog, text="确定", command=on_ok)
        btn.pack(pady=8)
        btn.update_idletasks()
        # 保证按钮完全显示
        dialog.minsize(w, h)
        qty_entry.focus_set()
        dialog.wait_window()
        return result['qty']
