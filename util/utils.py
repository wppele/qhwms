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
def set_pdf_chinese_font(pdfmetrics, TTFont):
    """
    注册PDF中文字体，优先使用微软雅黑，其次黑体。
    返回(font_title, font_normal)
    """
    import os
    font_path = None
    for fname in ["msyh.ttf", "simhei.ttf"]:
        for dir in [os.getcwd(), os.path.join(os.environ.get("WINDIR", r"C:\\Windows"), "Fonts")]:
            fpath = os.path.join(dir, fname)
            if os.path.exists(fpath):
                font_path = fpath
                break
        if font_path:
            break
    if font_path:
        pdfmetrics.registerFont(TTFont("zhfont", font_path))
        font_title = "zhfont"
        font_normal = "zhfont"
    else:
        font_title = "Helvetica-Bold"
        font_normal = "Helvetica"
    return font_title, font_normal
