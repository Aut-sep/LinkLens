# main.py

import threading
import time
import traceback
import sys

from backend.mouse_read import TextReader
from backend.summary_bot import SummaryBot
from frontend.float_window import show_floating
from PyQt5 import QtWidgets, QtCore
from frontend.config_window import ConfigWindow
from pynput import keyboard


class MainProcessor(QtCore.QObject):
    """
    这里把 MainProcessor 改为 QObject，方便接收 ConfigWindow.hotkeyChanged 信号。
    """
    def __init__(self):
        super().__init__()
        print("🔄 初始化 MainProcessor...")

        self.text_reader = TextReader()
        print("✅ TextReader 初始化完成")

        self.summary_bot = SummaryBot()
        print("✅ SummaryBot 初始化完成")

        # 初始热键由 settings.json 决定
        from settings import Settings
        self.settings = Settings()
        initial_hotkey = self.settings.get("hotkey", "Alt+Shift+Q")
        self._register_hotkey_listener(initial_hotkey)

    def _register_hotkey_listener(self, qt_key_str: str):
        """
        根据 QtKeySequence 字符串 (如 "Alt+Shift+Q") 转成 pynput 需要的格式，
        然后创建 GlobalHotKeys 并 start()。
        """
        # 如果之前有监听器，就先停止
        try:
            if hasattr(self, "hotkey_listener") and self.hotkey_listener:
                self.hotkey_listener.stop()
        except:
            pass

        # 把 qt_key_str 转换为 pynput 格式
        pynput_str = self._convert_qtstr_to_pynput(qt_key_str)
        if not pynput_str:
            print(f"⚠️ 无效的初始热键：{qt_key_str}")
            return

        print(f"🔑 注册热键监听：{pynput_str}")
        self.hotkey_listener = keyboard.GlobalHotKeys({
            pynput_str: self._trigger_and_summarize,
            "<alt>+<shift>+w": self.text_reader.stop
        })
        # 后台线程启动
        self.hotkey_listener.start()

    def _convert_qtstr_to_pynput(self, qt_str: str) -> str:
        parts = qt_str.split("+")
        mapping = {
            "Ctrl": "ctrl",
            "Control": "ctrl",
            "Alt": "alt",
            "Shift": "shift",
            "Cmd": "cmd",
            "Meta": "cmd"
        }
        out = []
        for part in parts:
            p = part.strip()
            if p in mapping:
                out.append(f"<{mapping[p]}>")
            else:
                out.append(p.lower())
        return "+".join(out)

    def _process_text_and_write(self, text: str, tmp_path: str):
        if not text:
            summary = "\n⚠️ 没有读取到文本"
        else:
            print(f"📥 文本: {repr(text)}")
            if self.text_reader._is_url(text):
                print("🔗 检测到有效URL，开始处理...")
                summary = self.summary_bot.get_summary(text)
                if summary:
                    print("📝 摘要生成成功")
                else:
                    summary = "⚠️ 摘要生成失败"
            else:
                summary = f"❌ 不是有效的URL: {repr(text)}"

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(summary)
        except Exception as e:
            print(f"❌ 无法写入临时文件 {tmp_path}：{e}")

    def _trigger_and_summarize(self):
        text = ""
        try:
            text = self.text_reader.read_selected_text(print_result=True)
        except Exception as e:
            print(f"❌ 读取剪贴板时出错: {e}")
            text = ""

        import os, uuid, tempfile
        uuid_str = str(uuid.uuid4())
        tmp_path = os.path.join(tempfile.gettempdir(), f"float_{uuid_str}.txt")
        try:
            with open(tmp_path, "w", encoding="utf-8"):
                pass
        except Exception as e:
            print(f"❌ 无法创建临时文件 {tmp_path}：{e}")
            return

        print(f"🌀 弹出“加载中…”悬浮窗，UUID={uuid_str}")
        show_floating(f"LOADING::{uuid_str}")

        worker = threading.Thread(
            target=self._process_text_and_write,
            args=(text, tmp_path),
            daemon=True
        )
        worker.start()

    def run(self):
        """
        之所以不把 join() 放在这里，是因为我们希望能够响应来自 ConfigWindow.hotkeyChanged 的信号，
        动态重置监听。因此，这里仅打印提示，监听器由 _register_hotkey_listener 启动。
        """
        print("🔥 热键监听器已启动")
        print("⏳ 现在可以选中文本后按热键读取")
        # 进入一个循环，保持线程存活
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            try:
                self.text_reader.stop()
            except:
                pass
            print("🛑 程序被用户中断，正在退出...")
        except Exception as e:
            print(f"⚠️ 监听线程异常: {e}")
            traceback.print_exc()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # —— 1. 实例化 ConfigWindow 并显示 —— #
    config_win = ConfigWindow()
    config_win.show()

    # —— 2. 实例化 MainProcessor —— #
    processor = MainProcessor()

    # —— 3. 连接 ConfigWindow.hotkeyChanged 信号 —— #
    def on_hotkey_updated(pynput_str: str):
        """
        先把 pynput_str 转回 QtKeySequence 形式，方便调用注册函数。
        例："<alt>+<shift>+q" → "Alt+Shift+Q"
        """
        mapping_inv = {
            "ctrl": "Ctrl",
            "alt": "Alt",
            "shift": "Shift",
            "cmd": "Meta"
        }
        parts = pynput_str.split("+")
        qt_parts = []
        for part in parts:
            if part.startswith("<") and part.endswith(">"):
                key = part[1:-1]
                qt_parts.append(mapping_inv.get(key, key.capitalize()))
            else:
                qt_parts.append(part.upper())
        qt_seq = "+".join(qt_parts)
        # 重新注册热键监听
        processor._register_hotkey_listener(qt_seq)

    config_win.hotkeyChanged.connect(on_hotkey_updated)

    # —— 4. 后台线程运行 processor.run() —— #
    threading.Thread(target=processor.run, daemon=True).start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
