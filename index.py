import tkinter as tk
from tkinter import ttk
from utils import center_window
from stock_page import StockPage
from log_page import LogPage

def show_main_page(username, root=None):
    if root is not None:
        main_win = tk.Toplevel(root)
    else:
        main_win = tk.Toplevel()
    main_win.title("千辉库房管理系统")
    main_win.state('zoomed')  # 默认最大化
    center_window(main_win, 800, 500)

    # 顶部栏（仅欢迎语，无选择框）
    top_frame = ttk.Frame(main_win)
    top_frame.pack(fill=tk.X, pady=5)
    right_top_frame = ttk.Frame(top_frame)
    right_top_frame.pack(side=tk.RIGHT)
    ttk.Label(right_top_frame, text=f"欢迎，{username}", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=10)

    # 主体区域
    main_frame = ttk.Frame(main_win)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 左侧侧滑栏（可收缩，按钮始终在栏目右侧）
    nav_container = ttk.Frame(main_frame)
    nav_container.pack(side=tk.LEFT, fill=tk.Y)
    nav_frame = ttk.Frame(nav_container)
    nav_frame.pack(side=tk.LEFT, fill=tk.Y)
    nav_tree = ttk.Treeview(nav_frame, show="tree", selectmode="browse", height=20)
    nav_tree.pack(fill=tk.Y, expand=True, padx=5, pady=5)
    # 添加菜单项（去除结账，保留库存和操作记录）
    up_id = nav_tree.insert('', 'end', text='上游厂商', open=True)
    nav_tree.insert(up_id, 'end', text='库存', iid='up_stock')
    nav_tree.insert(up_id, 'end', text='操作记录', iid='up_log')

    # 收缩/展开按钮，始终在左侧
    def toggle_nav():
        if nav_frame.winfo_ismapped():
            nav_frame.pack_forget()
            toggle_btn.config(text='▶')
        else:
            nav_frame.pack(side=tk.LEFT, fill=tk.Y)
            toggle_btn.config(text='◀')
    toggle_btn = ttk.Button(nav_container, text='◀', width=2, command=toggle_nav)
    toggle_btn.pack(side=tk.RIGHT, fill=tk.Y)

    # 右侧内容区
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 各功能页面Frame
    page_stock = StockPage(content_frame, main_win)
    page_log = LogPage(content_frame)
    # 页面切换逻辑
    def show_page(page):
        for f in (page_stock, page_log):
            f.pack_forget()
        page.pack(fill=tk.BOTH, expand=True)
    def on_nav_select(event):
        sel = nav_tree.selection()
        if not sel:
            return
        sel = sel[0]
        if sel == 'up_stock':
            show_page(page_stock)
        elif sel == 'up_log':
            show_page(page_log)
    nav_tree.bind('<<TreeviewSelect>>', on_nav_select)
    # 默认显示库存
    nav_tree.selection_set('up_stock')
    show_page(page_stock)

    # 退出按钮关闭所有窗口
    def quit_all():
        if root is not None:
            try:
                root.quit()
            except Exception:
                pass
            try:
                root.destroy()
            except Exception:
                pass
        try:
            main_win.destroy()
        except Exception:
            pass
    main_win.protocol("WM_DELETE_WINDOW", quit_all)

if __name__ == "__main__":
    r = tk.Tk()
    show_main_page("admin", r)
    r.mainloop()
