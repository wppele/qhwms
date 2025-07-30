import tkinter as tk
from tkinter import ttk, messagebox
from util import dbutil
from util.utils import center_window

def CustomerPage(parent):
    frame = ttk.Frame(parent)
    # 工具栏
    toolbar = ttk.Frame(frame)
    toolbar.pack(fill=tk.X, pady=5)
    # 图标按钮
    btn_add = ttk.Button(toolbar, text="➕", width=3)
    btn_add.pack(side=tk.LEFT, padx=3)
    btn_edit = ttk.Button(toolbar, text="✏️", width=3)
    btn_edit.pack(side=tk.LEFT, padx=3)
    btn_del = ttk.Button(toolbar, text="🗑️", width=3)
    btn_del.pack(side=tk.LEFT, padx=3)
    # tooltip
    def add_tooltip(widget, text):
        tip = tk.Toplevel(widget)
        tip.withdraw()
        tip.overrideredirect(True)
        label = tk.Label(tip, text=text, background="#ffffe0", relief=tk.SOLID, borderwidth=1, font=("微软雅黑", 9))
        label.pack(ipadx=4)
        def enter(event):
            x, y, cx, cy = widget.bbox("insert") if hasattr(widget, 'bbox') else (0, 0, 0, 0)
            x += widget.winfo_rootx() + 30
            y += widget.winfo_rooty() + 20
            tip.geometry(f"+{x}+{y}")
            tip.deiconify()
        def leave(event):
            tip.withdraw()
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
    add_tooltip(btn_add, "新增客户")
    add_tooltip(btn_edit, "修改客户信息")
    add_tooltip(btn_del, "删除客户信息")
    # 表格
    columns = ("no", "name", "address", "phone", "logistics_info")
    headers = [
        ("no", "序号"),
        ("name", "姓名"),
        ("address", "地址"),
        ("phone", "电话"),
        ("logistics_info", "物流信息")
    ]
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    for col, text in headers:
        if col == "logistics_info":
            tree.heading(col, text=text)
            tree.column(col, anchor=tk.CENTER, width=310)
        else:
            tree.heading(col, text=text)
            tree.column(col, anchor=tk.CENTER, width=30)
    def load_data():
        for row in tree.get_children():
            tree.delete(row)
        for idx, row in enumerate(dbutil.get_all_customers(), 1):
            # row: (id, name, address, phone, logistics_info)
            tree.insert("", tk.END, values=(idx, *row[1:]))
    frame.refresh = load_data
    load_data()
    # 新增客户
    def open_add_dialog():
        dialog = tk.Toplevel(frame)
        dialog.title("新增客户")
        dialog.transient(frame)
        dialog.grab_set()
        center_window(dialog, 400, 320)
        fields = [
            ("姓名", "name"),
            ("地址", "address"),
            ("电话", "phone")
        ]
        vars = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(dialog, text=label+":").grid(row=idx, column=0, sticky=tk.W, padx=10, pady=6)
            var = tk.StringVar()
            ttk.Entry(dialog, textvariable=var, width=30).grid(row=idx, column=1, padx=5)
            vars[key] = var
        # 物流信息动态输入
        logistics_entries = []
        def add_logistics_entry(default_val=""):
            row = len(fields) + len(logistics_entries)
            entry_var = tk.StringVar(value=default_val)
            entry = ttk.Entry(dialog, textvariable=entry_var, width=30)
            entry.grid(row=row, column=1, padx=(5,0), pady=2, sticky=tk.W)
            logistics_entries.append(entry_var)
        # 初始一个物流信息输入框
        ttk.Label(dialog, text="物流信息:").grid(row=len(fields), column=0, sticky=tk.W, padx=10, pady=6)
        add_logistics_entry()
        def on_add_logistics():
            add_logistics_entry()
        btn_add_logistics = ttk.Button(dialog, text="➕", width=2, command=on_add_logistics)
        btn_add_logistics.grid(row=len(fields), column=2, padx=(2,10), sticky=tk.W)
        def on_ok():
            if not vars['name'].get().strip():
                messagebox.showwarning("提示", "姓名不能为空！")
                return
            logistics_info = ";".join([v.get().strip() for v in logistics_entries if v.get().strip()])
            dbutil.insert_customer(
                vars['name'].get().strip(),
                vars['address'].get().strip(),
                vars['phone'].get().strip(),
                logistics_info
            )
            dialog.destroy()
            load_data()
            messagebox.showinfo("成功", "新增客户成功！")
        ttk.Button(dialog, text="确定", command=on_ok, width=12).grid(row=6+len(logistics_entries), column=0, columnspan=3, pady=12)
        dialog.wait_window()
    btn_add.config(command=open_add_dialog)
    # 修改客户
    def open_edit_dialog():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要修改的客户！")
            return
        item = tree.item(selected[0])
        values = item['values']
        dialog = tk.Toplevel(frame)
        dialog.title("修改客户信息")
        dialog.transient(frame)
        dialog.grab_set()
        center_window(dialog, 400, 320)
        fields = [
            ("姓名", "name"),
            ("地址", "address"),
            ("电话", "phone")
        ]
        vars = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(dialog, text=label+":").grid(row=idx, column=0, sticky=tk.W, padx=10, pady=6)
            var = tk.StringVar(value=values[idx+1])
            ttk.Entry(dialog, textvariable=var, width=30).grid(row=idx, column=1, padx=5)
            vars[key] = var
        # 物流信息动态输入
        logistics_entries = []
        logistics_list = values[4].split(';') if values[4] else ['']
        ttk.Label(dialog, text="物流信息:").grid(row=len(fields), column=0, sticky=tk.W, padx=10, pady=6)
        def add_logistics_entry_edit(default_val=""):
            row = len(fields) + len(logistics_entries)
            entry_var = tk.StringVar(value=default_val)
            entry = ttk.Entry(dialog, textvariable=entry_var, width=30)
            entry.grid(row=row, column=1, padx=(5,0), pady=2, sticky=tk.W)
            logistics_entries.append(entry_var)
        for l in logistics_list:
            add_logistics_entry_edit(l)
        def on_add_logistics():
            add_logistics_entry_edit()
        btn_add_logistics = ttk.Button(dialog, text="➕", width=2, command=on_add_logistics)
        btn_add_logistics.grid(row=len(fields), column=2, padx=(2,10), sticky=tk.W)
        def on_ok():
            if not vars['name'].get().strip():
                messagebox.showwarning("提示", "姓名不能为空！")
                return
            logistics_info = ";".join([v.get().strip() for v in logistics_entries if v.get().strip()])
            # 用 tree.item 的 iid 获取真实主键
            cid = tree.item(selected[0], 'values')[0]
            all_rows = dbutil.get_all_customers()
            for idx, row in enumerate(all_rows, 1):
                if str(idx) == str(cid):
                    real_id = row[0]
                    break
            else:
                real_id = cid
            dbutil.update_customer(
                real_id,
                vars['name'].get().strip(),
                vars['address'].get().strip(),
                vars['phone'].get().strip(),
                logistics_info
            )
            dialog.destroy()
            load_data()
            messagebox.showinfo("成功", "修改成功！")
        ttk.Button(dialog, text="确定", command=on_ok, width=12).grid(row=6+len(logistics_entries), column=0, columnspan=3, pady=12)
        dialog.wait_window()
    btn_edit.config(command=open_edit_dialog)
    # 删除客户
    def on_delete():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的客户！")
            return
        item = tree.item(selected[0])
        cid = item['values'][0]
        # 查找真实主键id
        all_rows = dbutil.get_all_customers()
        for idx, row in enumerate(all_rows, 1):
            if str(idx) == str(cid):
                real_id = row[0]
                break
        else:
            real_id = cid
        if not messagebox.askyesno("确认", "确定要删除该客户信息吗？"):
            return
        dbutil.delete_customer(real_id)
        load_data()
        messagebox.showinfo("成功", "删除成功！")
    btn_del.config(command=on_delete)
    return frame
