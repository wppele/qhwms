import tkinter as tk
from tkinter import ttk, messagebox
from util.utils import center_window
from pages.stock_page import StockPage
from pages.record_pages import SettleLogPage, StockLogPage
from pages.inventory_page import InventoryPage  # 新增库存页面导入
from pages.customer_page import CustomerPage
from pages.account_manage_page import AccountManagePage
from pages.outbound_manage_page import OutboundManagePage
from pages.sale_return_page import SaleReturnPage
from pages.welcome_page import WelcomeFrame
from pages.payment_record_page import PaymentRecordPage
from pages.arrears_settle_page import ArrearsSettlePage
from pages.customer_statement_page import CustomerStatementPage
from util.dbutil import get_user_unipassword_by_username

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
    style = ttk.Style()
    style.configure('Sidebar.Treeview',
                    font=("微软雅黑", 14, "bold"),
                    rowheight=38)
    style.configure('Sidebar.Treeview.Heading', font=("微软雅黑", 15, "bold"))
    # 选中项字体颜色鲜艳（如蓝色），背景色高亮
    style.map('Sidebar.Treeview',
              background=[('selected', '#00bcd4')],
              foreground=[('selected', '#fffb00')])  # 黄色字体
    nav_tree = ttk.Treeview(nav_frame, show="tree", selectmode="browse", height=20, style='Sidebar.Treeview')
    nav_tree.pack(fill=tk.Y, expand=True, padx=5, pady=5)
    # 侧边栏整体背景色
    nav_frame.configure(style='Sidebar.TFrame')
    style.configure('Sidebar.TFrame', background='#f5f7fa')
    # 添加菜单项（采购管理、销售管理、客户信息）
    up_id = nav_tree.insert('', 'end', text='采购管理', open=False)  # 默认为闭合
    nav_tree.insert(up_id, 'end', text='采购入库', iid='up_stock')
    nav_tree.insert(up_id, 'end', text='结账记录', iid='settle_log')
    nav_tree.insert(up_id, 'end', text='入库/返厂记录', iid='stock_log')

    # 销售管理为一级菜单，包含销售开单、出库单管理、销售退换货、收款结算
    sale_id = nav_tree.insert('', 'end', text='销售管理', open=False)
    nav_tree.insert(sale_id, 'end', text='开单|库存', iid='inventory')
    nav_tree.insert(sale_id, 'end', text='出库单管理', iid='outbound_manage')
    nav_tree.insert(sale_id, 'end', text='付款记录查询', iid='payment_record_query')
    nav_tree.insert(sale_id, 'end', text='销售退货', iid='sale_return')
    nav_tree.insert(sale_id, 'end', text='余款结算', iid='arrears_settle')
    nav_tree.insert(sale_id, 'end', text='客户对账单', iid='customer_statement')

    # 基础信息管理为一级菜单，包含客户信息、账户管理
    base_id = nav_tree.insert('', 'end', text='基础信息管理', open=False)
    nav_tree.insert(base_id, 'end', text='客户信息', iid='customer_info')
    nav_tree.insert(base_id, 'end', text='账户管理', iid='account_manage')

    # 收缩/展开按钮，始终在左侧
    def toggle_nav():
        if nav_frame.winfo_ismapped():
            nav_frame.pack_forget()
            toggle_btn.config(text='▶')
        else:
            nav_frame.pack(side=tk.LEFT, fill=tk.Y)
            toggle_btn.config(text='◀')
    toggle_btn = ttk.Button(nav_container, text='◀', width=2, command=toggle_nav, style='Sidebar.TButton')
    style.configure('Sidebar.TButton', font=("微软雅黑", 13, "bold"), background='#e0f7fa', foreground='#1a3d1a')
    toggle_btn.pack(side=tk.RIGHT, fill=tk.Y, padx=2, pady=2)

    # 右侧内容区
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 欢迎页Frame
    welcome_frame = WelcomeFrame(content_frame)
    welcome_frame.pack(fill=tk.BOTH, expand=True)

    # 页面延迟初始化字典
    pages = {}
    page_classes = {
        'stock': (StockPage, (content_frame, main_win)),
        'settle_log': (SettleLogPage, (content_frame,)),
        'stock_log': (StockLogPage, (content_frame,)),
        'inventory': (InventoryPage, (content_frame,)),
        'customer': (CustomerPage, (content_frame, username)),
        'account_manage': (AccountManagePage, (content_frame,)),
        'outbound_manage': (OutboundManagePage, (content_frame,)),
        'payment_record': (PaymentRecordPage, (content_frame,)),
        'arrears_settle': (ArrearsSettlePage, (content_frame,)),
        'customer_statement': (CustomerStatementPage, (content_frame,)),
        'sale_return': (SaleReturnPage, (content_frame,))
    }

    # 页面切换逻辑
    def show_page(page_key):
        # 先隐藏所有已创建的页面
        for f in list(pages.values()) + [welcome_frame]:
            f.pack_forget()

        # 如果页面未初始化，则创建它
        if page_key not in pages:
            page_class, args = page_classes[page_key]
            pages[page_key] = page_class(*args)
            # 确保新创建的页面正确初始化
            content_frame.update_idletasks()

        # 显示选中的页面
        page = pages[page_key]
        page.pack(fill=tk.BOTH, expand=True)
        # 确保页面在最顶层
        page.lift()
        # 确保页面获得焦点
        page.focus_set()
        # 刷新页面数据
        if hasattr(page, 'refresh'):
            page.refresh()
        # 强制重绘
        content_frame.update()
        content_frame.update_idletasks()

    # 默认显示欢迎页
    # 欢迎页不参与延迟初始化，保持原样
    welcome_frame.pack(fill=tk.BOTH, expand=True)
    welcome_frame.lift()
    welcome_frame.focus_set()
    content_frame.update_idletasks()
    # 不选中任何菜单项，等用户点击后再切换页面

    # 提供全局刷新方法供库存页面调用
    def refresh_logs():
        if 'settle_log' in pages:
            pages['settle_log'].refresh()
        if 'stock_log' in pages:
            pages['stock_log'].refresh()
    main_win.refresh_logs = refresh_logs

    def on_nav_select(event):
        sel = nav_tree.selection()
        if not sel:
            return
        sel = sel[0]
        if sel == 'up_stock':
            show_page('stock')
        elif sel == 'settle_log':
            show_page('settle_log')
        elif sel == 'stock_log':
            show_page('stock_log')
        elif sel == 'inventory':  # 销售开单
            show_page('inventory')
        elif sel == 'customer_info':
            # 检查当前用户的unipassword
            from util.dbutil import get_user_unipassword_by_username
            unipassword = get_user_unipassword_by_username(username)
            
            if not unipassword or unipassword.strip() == '':
                # 如果unipassword为空，直接打开客户信息页面
                show_page('customer')
            else:
                # 如果unipassword不为空，弹出密码输入框
                def check_password():
                    password = password_entry.get()
                    if password == unipassword:
                        password_window.destroy()
                        show_page('customer')
                    else:
                        messagebox.showerror("错误", "密码输入错误，请重试！")
                        password_entry.delete(0, tk.END)
                        password_entry.focus_set()
                
                password_window = tk.Toplevel(main_win)
                password_window.title("密码验证")
                password_window.resizable(False, False)
                password_window.grab_set()  # 模态窗口
                center_window(password_window, 300, 150)
                
                ttk.Label(password_window, text="请输入密码:", font=('微软雅黑', 12)).pack(pady=20)
                password_entry = ttk.Entry(password_window, show='*', width=20)
                password_entry.pack(pady=5)
                password_entry.focus_set()
                # 绑定回车键到确定按钮
                password_entry.bind('<Return>', lambda event: check_password())
                
                btn_frame = ttk.Frame(password_window)
                btn_frame.pack(pady=10)
                ttk.Button(btn_frame, text="确定", command=check_password).pack(side=tk.LEFT, padx=10)
                ttk.Button(btn_frame, text="取消", command=password_window.destroy).pack(side=tk.LEFT)
        elif sel == 'account_manage':
            show_page('account_manage')
        elif sel == 'outbound_manage':
            show_page('outbound_manage')
        elif sel == 'payment_record_query':
            show_page('payment_record')
        elif sel == 'sale_return':
            show_page('sale_return')
        elif sel == 'arrears_settle':
            show_page('arrears_settle')
        elif sel == 'customer_statement':
            show_page('customer_statement')
    nav_tree.bind('<<TreeviewSelect>>', on_nav_select)
    # 不自动选中任何菜单项

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
