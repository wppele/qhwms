import tkinter as tk
from tkinter import ttk, messagebox
from util import dbutil
from pages.index import show_main_page
from util.utils import center_window

# 登录窗口
def show_login_window():
    dbutil.init_db()
    root = tk.Tk()
    root.title("登录")
    center_window(root, 300, 180)

    # 顶部标题
    ttk.Label(root, text="千辉鞋业仓库管理系统", font=("微软雅黑", 15, "bold"), foreground="#2a5caa").pack(pady=(18, 8))
    # 用户名和密码同一行显示
    form_frame = ttk.Frame(root)
    form_frame.pack(pady=(5, 10))
    # 用户名
    ttk.Label(form_frame, text="用户名:").grid(row=0, column=0, padx=(0, 8), pady=5, sticky=tk.E)
    username_var = tk.StringVar()
    username_entry = ttk.Entry(form_frame, textvariable=username_var, width=18)
    username_entry.grid(row=0, column=1, pady=5)
    username_entry.focus_set()
    # 密码
    ttk.Label(form_frame, text="密码:").grid(row=1, column=0, padx=(0, 8), pady=5, sticky=tk.E)
    password_var = tk.StringVar()
    password_entry = ttk.Entry(form_frame, textvariable=password_var, show="*", width=18)
    password_entry.grid(row=1, column=1, pady=5)

    def on_login():
        username = username_var.get()
        password = password_var.get()
        if dbutil.check_user(username, password):
            root.withdraw()
            username = dbutil.get_username_by_account(username)
            show_main_page(username, root)
        else:
            messagebox.showerror("登录失败", "用户名或密码错误！")

    ttk.Button(root, text="登录", command=on_login).pack(pady=(2, 5))
    root.bind('<Return>', lambda event: on_login())
    root.mainloop()


def main():
    show_login_window()


if __name__ == "__main__":
    main()
