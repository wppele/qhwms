# 欢迎页面
from tkinter import ttk

class WelcomeFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="欢迎使用千辉鞋业仓库管理系统！", font=("微软雅黑", 18, "bold"), foreground="#2a5d2a").pack(pady=(60, 20))
        ttk.Label(self, text="请通过左侧菜单进行操作。", font=("微软雅黑", 13)).pack(pady=10)
        ttk.Label(self, text="如有疑问请联系管理员。", font=("微软雅黑", 11), foreground="#888").pack(pady=10)
