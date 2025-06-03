# frontend/float_window.py

import sys
import subprocess
import os
from urllib.parse import quote_plus

def show_floating(text=None):
    """
    每次都启动一个新的 Python 子进程去跑 float_window_app.py，
    这样里面的 QApplication 就一定在子进程的主线程中创建。
    """
    # 1. 找到 float_window_app.py 的绝对路径
    this_dir = os.path.dirname(os.path.abspath(__file__))
    launcher = os.path.join(this_dir, "float_window_app.py")

    # 2. 对文本做 URL encode，防止空格和特殊字符导致命令行拆分
    param = quote_plus(text or "")

    # 3. 用 sys.executable 保证当前 Python 解释器（如果你 activate 了 conda/env）
    #    Popen 时不要 wait，直接异步弹出
    try:
        subprocess.Popen([sys.executable, launcher, param])
    except Exception as e:
        print(f"❌ 无法启动悬浮窗进程: {e}")
