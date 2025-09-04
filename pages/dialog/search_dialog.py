# 商品搜索对话框页面
import tkinter as tk
from tkinter import ttk, messagebox
from util import dbutil
from util.utils import center_window

class ProductSearchDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("搜索商品")
        # 使用center_window方法居中窗口
        center_window(self, 600, 400)
        self.transient(parent)
        self.grab_set()
        self.parent = parent
        self.selected_product = None
        self.setup_ui()
        self.load_all_products()
        # 不使用wait_window()，因为它会阻塞事件处理
        # self.wait_window()

    def setup_ui(self):
        # 搜索框
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(search_frame, text="货号搜索: ").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.focus_set()

        ttk.Button(search_frame, text="搜索", command=self.search_products).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="显示全部", command=self.load_all_products).pack(side=tk.LEFT)

        # 商品列表 - 带滚动条
        columns = ("product_no", "color", "unit", "size", "stock")
        headers = [
            ("product_no", "货号"),
            ("color", "颜色"),
            ("unit", "单位"),
            ("size", "尺码"),
            ("stock", "库存")
        ]

        # 创建一个框架来放置Treeview和滚动条
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建滚动条
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建Treeview并关联滚动条
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10, yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 配置滚动条
        scrollbar.config(command=self.tree.yview)

        for col, text in headers:
            self.tree.heading(col, text=text)
            width = 100 if col != "product_no" else 150
            self.tree.column(col, anchor=tk.CENTER, width=width)

        # 绑定双击事件
        self.tree.bind('<Double-1>', self.on_double_click)

        # 底部按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="添加选中", command=self.add_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.LEFT, padx=5)

        # 绑定回车键搜索
        search_entry.bind('<Return>', lambda e: self.search_products())

    def load_all_products(self):
        """加载所有商品"""
        self.clear_tree()
        all_inv = dbutil.get_all_inventory()
        for inv in all_inv:
            # inv[0] = id, inv[3] = product_no, inv[5] = color, inv[6] = unit, inv[4] = size, inv[-1] = stock
            self.tree.insert('', tk.END, values=(inv[3], inv[5], inv[6], inv[4], inv[-1]), tags=(inv[0],))

    def search_products(self):
        """根据货号搜索商品"""
        keyword = self.search_var.get().strip().lower()
        if not keyword:
            self.load_all_products()
            return

        self.clear_tree()
        all_inv = dbutil.get_all_inventory()
        for inv in all_inv:
            product_no = inv[3].lower()
            if keyword in product_no:
                self.tree.insert('', tk.END, values=(inv[3], inv[5], inv[6], inv[4], inv[-1]), tags=(inv[0],))

    def clear_tree(self):
        """清空商品列表"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def on_double_click(self, event):
        """双击添加商品"""
        self.add_selected()

    def add_selected(self):
        """添加选中的商品"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择商品")
            return

        item = selected[0]
        product_id = self.tree.item(item, "tags")[0]
        product_no = self.tree.item(item, "values")[0]
        color = self.tree.item(item, "values")[1]
        unit = self.tree.item(item, "values")[2]
        size = self.tree.item(item, "values")[3]

        # 设置选中的商品
        self.selected_product = {
            'id': product_id,
            'product_no': product_no,
            'color': color,
            'unit': unit,
            'size': size
        }

        # 触发商品选中事件
        self.event_generate('<<ProductSelected>>')

        # 保持窗口打开，不隐藏，以便连续添加商品
        # 清空选中项，准备下次选择
        self.tree.selection_remove(selected)

    def get_selected_product(self):
        """获取选中的商品"""
        return self.selected_product

    def destroy(self):
        """销毁窗口"""
        super().destroy()

    def withdraw(self):
        """隐藏窗口"""
        # 确保在隐藏前释放抓取
        if self.grab_status() == "global":
            self.grab_release()
        super().withdraw()
        # 隐藏后激活父窗口
        if self.parent and self.parent.winfo_exists():
            self.parent.focus_set()

    def deiconify(self):
        """显示窗口"""
        super().deiconify()
        center_window(self, 600, 400)
        # 重新设置抓取
        self.grab_set()
        # 确保窗口获得焦点
        self.focus_force()
# 使用示例
# def open_search_dialog(parent):
#     dialog = ProductSearchDialog(parent)
#     product = dialog.get_selected_product()
#     if product:
#         print(f"选中商品: {product}")