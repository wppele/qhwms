from datetime import datetime

def center_window(window, width=300, height=180):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def calculate_total(quantity, price):
    """计算库存项目总价(数量×单价)"""
    try:
        total = float(quantity or 0) * float(price or 0)
        return f"{total:.2f}"
    except ValueError:
        return "0.00"

def get_current_date():
    """返回当前日期，格式为YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")
