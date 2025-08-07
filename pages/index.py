import tkinter as tk
from tkinter import ttk
from util.utils import center_window
from pages.stock_page import StockPage
from pages.record_pages import SettleLogPage, StockLogPage
from pages.inventory_page import InventoryPage  # 新增库存页面导入
from pages.customer_page import CustomerPage
from pages.account_manage_page import AccountManagePage

from pages.outbound_manage_page import OutboundManagePage
from pages.sale_return_page import SaleReturnPage
from pages.welcome_page import WelcomeFrame

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

    # 各功能页面Frame
    page_stock = StockPage(content_frame, main_win)
    page_settle_log = SettleLogPage(content_frame)
    page_stock_log = StockLogPage(content_frame)
    page_inventory = InventoryPage(content_frame)  # 新增库存页面实例
    page_customer = CustomerPage(content_frame)
    page_account_manage = AccountManagePage(content_frame)
    page_outbound_manage = OutboundManagePage(content_frame)
    from pages.payment_record_page import PaymentRecordPage
    page_payment_record = PaymentRecordPage(content_frame)
    from pages.arrears_settle_page import ArrearsSettlePage
    page_arrears_settle = ArrearsSettlePage(content_frame)
    from pages.customer_statement_page import CustomerStatementPage
    page_customer_statement = CustomerStatementPage(content_frame)
    page_sale_return = SaleReturnPage(content_frame)

    # 页面切换逻辑
    def show_page(page):
        for f in (welcome_frame, page_stock, page_settle_log, page_stock_log, page_inventory, page_customer, page_outbound_manage, page_payment_record, page_arrears_settle, page_sale_return, page_account_manage, page_customer_statement):
            f.pack_forget()
        page.pack(fill=tk.BOTH, expand=True)
        # 切换到日志页面时自动刷新
        if hasattr(page, 'refresh'):
            page.refresh()

    # 默认显示欢迎页
    show_page(welcome_frame)
    # 不选中任何菜单项，等用户点击后再切换页面

    # 提供全局刷新方法供库存页面调用
    main_win.refresh_logs = lambda: [page_settle_log.refresh(), page_stock_log.refresh()]

    def on_nav_select(event):
        sel = nav_tree.selection()
        if not sel:
            return
        sel = sel[0]
        if sel == 'up_stock':
            show_page(page_stock)
        elif sel == 'settle_log':
            show_page(page_settle_log)
        elif sel == 'stock_log':
            show_page(page_stock_log)
        elif sel == 'inventory':  # 销售开单
            show_page(page_inventory)
        elif sel == 'customer_info':
            show_page(page_customer)
        elif sel == 'account_manage':
            show_page(page_account_manage)
        elif sel == 'outbound_manage':
            show_page(page_outbound_manage)
        elif sel == 'payment_record_query':
            show_page(page_payment_record)
        elif sel == 'sale_return':
            show_page(page_sale_return)
        elif sel == 'arrears_settle':
            show_page(page_arrears_settle)
        elif sel == 'customer_statement':
            show_page(page_customer_statement)
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
