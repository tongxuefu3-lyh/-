import tkinter as tk
import requests
import re
import os
import threading
import pystray
from PIL import Image, ImageDraw

CONFIG_FILE = "config.txt"

# ===== 读取上次股票 =====
def load_last_stock():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            code = f.read().strip()
            if code:
                return code
    return "sh600000"

def save_stock(code):
    with open(CONFIG_FILE, "w") as f:
        f.write(code)

stock_code = load_last_stock()
is_topmost = True
tray_icon = None


# ===== 获取股票数据 =====
def get_stock_data():
    url = f"http://hq.sinajs.cn/list={stock_code}"
    headers = {"Referer": "http://finance.sina.com.cn"}
    response = requests.get(url, headers=headers, timeout=5)
    response.encoding = "gbk"

    match = re.search(r'="(.*)"', response.text)
    if not match:
        return None

    info = match.group(1).split(",")
    if len(info) < 4:
        return None

    current_price = float(info[3])
    yesterday_close = float(info[2])
    return (current_price - yesterday_close) / yesterday_close * 100


def format_code(code):
    if code.startswith("6"):
        return "sh" + code
    elif code.startswith(("0", "3")):
        return "sz" + code
    return code


# ===== 更新界面 =====
def update():
    try:
        percent = get_stock_data()
        if percent is None:
            label.config(text="--")
        else:
            sign = "*" if percent >= 0 else "#"
            label.config(text=f"{stock_code[-6:]}\n{sign}{abs(percent):.2f}^")
    except:
        label.config(text="--")

    root.after(5000, update)


# ===== 设置窗口 =====
def open_settings(event=None):
    global stock_code, is_topmost

    win = tk.Toplevel(root)
    win.title("设置")
    win.geometry("230x160")
    win.resizable(False, False)

    tk.Label(win, text="输入密码：").pack(pady=(10, 4))

    entry = tk.Entry(win)
    entry.insert(0, stock_code[-6:])
    entry.pack()

    top_var = tk.BooleanVar(value=is_topmost)
    tk.Checkbutton(win, text="窗口置顶", variable=top_var).pack(pady=6)

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    def confirm():
        global stock_code, is_topmost

        code = entry.get().strip()
        if len(code) == 6 and code.isdigit():
            stock_code = format_code(code)
            save_stock(stock_code)

        is_topmost = top_var.get()
        root.attributes("-topmost", is_topmost)

        win.destroy()
        update()

    def hide_window():
        win.destroy()
        root.withdraw()

    tk.Button(btn_frame, text="确定", width=6, command=confirm).pack(side="left", padx=5)
    tk.Button(btn_frame, text="取消", width=6, command=win.destroy).pack(side="left", padx=5)
    tk.Button(btn_frame, text="隐藏", width=6, command=hide_window).pack(side="left", padx=5)


# ===== 托盘相关 =====
def create_image():
    img = Image.new("RGB", (64, 64), "white")
    d = ImageDraw.Draw(img)
    d.text((18, 18), "股", fill="black")
    return img

def show_window(icon=None, item=None):
    root.after(0, root.deiconify)

def hide_window_tray(icon=None, item=None):
    root.after(0, root.withdraw)

def exit_program(icon=None, item=None):
    global tray_icon
    if tray_icon:
        tray_icon.stop()
    root.destroy()

def setup_tray():
    global tray_icon
    tray_icon = pystray.Icon(
        "stock_tool",
        create_image(),
        "监控",
        menu=pystray.Menu(
            pystray.MenuItem("显示窗口", show_window),
            pystray.MenuItem("隐藏窗口", hide_window_tray),
            pystray.MenuItem("设置", lambda: root.after(0, open_settings)),
            pystray.MenuItem("退出", exit_program)
        )
    )
    tray_icon.run()


# ===== 拖动窗口 =====
def start_move(event):
    root.x = event.x
    root.y = event.y

def do_move(event):
    root.geometry(f"+{event.x_root - root.x}+{event.y_root - root.y}")


# ===== 主界面 =====
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", is_topmost)
root.geometry("100x60")
root.attributes("-alpha", 0.6)  # 透明度自己调

# 默认右下角
root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = screen_width - 110
y = screen_height - 100
root.geometry(f"+{x}+{y}")

label = tk.Label(
    root,
    text="加载中...",
    font=("Arial", 10),
    bg="white",
    justify="center"
)
label.pack(expand=True, fill="both")

label.bind("<Button-1>", start_move)
label.bind("<B1-Motion>", do_move)
label.bind("<Double-Button-1>", open_settings)

update()

threading.Thread(target=setup_tray, daemon=True).start()

root.mainloop()
