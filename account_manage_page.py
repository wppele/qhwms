import tkinter as tk
from tkinter import ttk, messagebox
from util import dbutil
from util.utils import center_window

class AccountManagePage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="账户管理", font=("微软雅黑", 16, "bold"), foreground="#2a5d2a").pack(pady=(20, 10))
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=24)
        ttk.Button(btn_frame, text="新增用户", command=self.add_user).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="编辑用户", command=self.edit_user).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="删除用户", command=self.delete_user).pack(side=tk.LEFT, padx=4)
        self.tree = ttk.Treeview(self, columns=("id", "username", "account", "role"), show="headings", height=10)
        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="用户名")
        self.tree.heading("account", text="账号")
        self.tree.heading("role", text="权限")
        self.tree.column("id", width=60, anchor=tk.CENTER)
        self.tree.column("username", width=120, anchor=tk.CENTER)
        self.tree.column("account", width=120, anchor=tk.CENTER)
        self.tree.column("role", width=100, anchor=tk.CENTER)
        self.tree.pack(fill=tk.X, padx=24, pady=8)
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in dbutil.get_all_users():
            role_text = "管理员" if row[3] == 0 else "库管"
            self.tree.insert('', tk.END, values=(row[0], row[1], row[2], role_text))

    def add_user(self):
        dialog = UserDialog(self, title="新增用户")
        self.wait_window(dialog)
        if dialog.result:
            username, account, password, role = dialog.result
            try:
                dbutil.insert_user(username, account, password, role)
                messagebox.showinfo("成功", "用户添加成功！")
                self.refresh()
            except Exception as e:
                messagebox.showerror("错误", f"添加失败：{e}")

    def edit_user(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择要编辑的用户！")
            return
        item = self.tree.item(sel[0])
        user_id, username, account, role_text = item['values']
        role = 0 if role_text == "管理员" else 1
        dialog = UserDialog(self, title="编辑用户", username=username, account=account, role=role)
        self.wait_window(dialog)
        if dialog.result:
            new_username, new_account, new_password, new_role = dialog.result
            try:
                dbutil.update_user(user_id, username=new_username, account=new_account, password=new_password if new_password else None, role=new_role)
                messagebox.showinfo("成功", "用户信息已更新！")
                self.refresh()
            except Exception as e:
                messagebox.showerror("错误", f"更新失败：{e}")

    def delete_user(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择要删除的用户！")
            return
        item = self.tree.item(sel[0])
        user_id = item['values'][0]
        if messagebox.askyesno("确认", "确定要删除该用户吗？"):
            try:
                dbutil.delete_user(user_id)
                messagebox.showinfo("成功", "用户已删除！")
                self.refresh()
            except Exception as e:
                messagebox.showerror("错误", f"删除失败：{e}")

class UserDialog(tk.Toplevel):
    def __init__(self, parent, title, username="", account="", role=1):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.geometry("320x220")
        self.resizable(False, False)
        center_window(self, 320, 220)
        # 用户名
        row1 = ttk.Frame(self)
        row1.pack(fill=tk.X, pady=6, padx=24)
        ttk.Label(row1, text="用户名:", width=8, anchor=tk.W).pack(side=tk.LEFT)
        self.entry_username = ttk.Entry(row1, width=18)
        self.entry_username.pack(side=tk.LEFT)
        self.entry_username.insert(0, username)
        # 账号
        row2 = ttk.Frame(self)
        row2.pack(fill=tk.X, pady=6, padx=24)
        ttk.Label(row2, text="账号:", width=8, anchor=tk.W).pack(side=tk.LEFT)
        self.entry_account = ttk.Entry(row2, width=18)
        self.entry_account.pack(side=tk.LEFT)
        self.entry_account.insert(0, account)
        # 密码
        row3 = ttk.Frame(self)
        row3.pack(fill=tk.X, pady=6, padx=24)
        ttk.Label(row3, text="密码:", width=8, anchor=tk.W).pack(side=tk.LEFT)
        self.entry_password = ttk.Entry(row3, show="*", width=18)
        self.entry_password.pack(side=tk.LEFT)
        # 权限
        row4 = ttk.Frame(self)
        row4.pack(fill=tk.X, pady=6, padx=24)
        ttk.Label(row4, text="权限:", width=8, anchor=tk.W).pack(side=tk.LEFT)
        self.role_var = tk.IntVar(value=role)
        ttk.Radiobutton(row4, text="管理员", variable=self.role_var, value=0).pack(side=tk.LEFT, padx=8)
        ttk.Radiobutton(row4, text="库管", variable=self.role_var, value=1).pack(side=tk.LEFT, padx=8)
        # 确定按钮
        btn = ttk.Button(self, text="确定", command=self.on_ok)
        btn.pack(pady=12)
        self.entry_username.focus_set()
        self.bind('<Return>', lambda e: self.on_ok())

    def on_ok(self):
        username = self.entry_username.get().strip()
        account = self.entry_account.get().strip()
        password = self.entry_password.get().strip()
        role = self.role_var.get()
        if not username or not account:
            messagebox.showwarning("提示", "用户名和账号不能为空！")
            return
        self.result = (username, account, password, role)
        self.destroy()
