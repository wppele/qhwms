import tkinter as tk
from tkinter import ttk, messagebox
from util import dbutil
from index import show_main_page
from utils import center_window


def show_login_window():
    dbutil.init_db()
    root = tk.Tk()
    root.title("登录")
    center_window(root, 300, 180)

    # 用户名
    ttk.Label(root, text="用户名:").pack(pady=(20, 5))
    username_var = tk.StringVar()
    username_entry = ttk.Entry(root, textvariable=username_var)
    username_entry.pack()

    # 密码
    ttk.Label(root, text="密码:").pack(pady=(10, 5))
    password_var = tk.StringVar()
    password_entry = ttk.Entry(root, textvariable=password_var, show="*")
    password_entry.pack()

    def on_login():
        username = username_var.get()
        password = password_var.get()
        if dbutil.check_user(username, password):
            root.withdraw()
            username = dbutil.get_username_by_account(username)
            show_main_page(username, root)
        else:
            messagebox.showerror("登录失败", "用户名或密码错误！")

    ttk.Button(root, text="登录", command=on_login).pack(pady=15)
    root.mainloop()


def main():
    show_login_window()


if __name__ == "__main__":
    main()
