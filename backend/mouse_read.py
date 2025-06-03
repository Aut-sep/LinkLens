# backend/mouse_read.py

import time
import re
import pyperclip
from frontend.float_window import show_floating  # 调用刚才改成子进程模式的模块
from pynput import keyboard
from urllib.parse import urlparse
from threading import Lock


class TextReader:
    def __init__(self):
        self.lock = Lock()
        self.keyboard = keyboard.Controller()
        # 初始化热键监听器
        self.hotkey_listener = keyboard.GlobalHotKeys(
            {
                "<alt>+<shift>+q": self.trigger_read,
                "<alt>+<shift>+w": self.stop,
            }
        )

    def trigger_read(self):
        """热键触发入口"""
        print("▶▶▶ trigger_read() 已被调用")    # debug
        with self.lock:
            # 先取到选中的文本
            text = self.read_selected_text()
            print(f"   — 读取到的文本: {repr(text)}")   # debug
            try:
                show_floating(text)
            except Exception as e:
                print(f"❌ show_floating 出现错误: {e}")    # debug

    def _is_url(self, text):
        """URL验证方法"""
        # 基本格式验证
        pattern = re.compile(
            r"^(?:http|ftp)s?://|^"  # 允许无协议头
            r"(?:www\.)?"  # 支持www前缀
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # 域名
            r"localhost|"  # 本地地址
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IPv4
            r"(?::\d+)?"  # 端口
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not re.match(pattern, text):
            return False

        # 结构化验证
        try:
            parsed = urlparse(text if "://" in text else f"http://{text}")
            return all([parsed.scheme, parsed.netloc]) and "." in parsed.netloc
        except:
            return False

    def read_selected_text(self, print_result=True):
        """读取逻辑（判断逻辑）
        Args:
            print_result (bool): 是否打印结果，默认为True
        Returns:
            str: 读取到的文本内容
        """
        try:
            original = pyperclip.paste()
            self.safe_release_keys()

            self.keyboard.press(keyboard.Key.ctrl)
            time.sleep(0.1)
            self.keyboard.press("c")
            time.sleep(0.15)
            self.keyboard.release("c")
            self.keyboard.release(keyboard.Key.ctrl)

            time.sleep(0.2)
            new_text = pyperclip.paste().strip()

            # 在输出前增加判断
            if print_result:
                if new_text:
                    status = "✅ 检测到URL" if self._is_url(new_text) else "📝 普通文本"
                    print(f"{status}: {new_text}")
                else:
                    print("⚠️ 未获取到有效内容")

            # 立即清除剪贴板
            pyperclip.copy("")
            time.sleep(0.1)
            pyperclip.copy(original)

            return new_text

        except Exception as e:
            if print_result:
                print(f"❌ 发生错误: {str(e)}")
            self.safe_release_keys()
            return None

    def get_selected_text(self):
        """获取选中的文本内容而不打印
        Returns:
            str: 读取到的文本内容（仅当是URL时返回）
        """
        text = self.read_selected_text(print_result=False)
        return text if text and self._is_url(text) else None

    def safe_release_keys(self):
        """安全释放按键"""
        for key in [keyboard.Key.ctrl, "c", keyboard.Key.alt, keyboard.Key.shift]:
            try:
                self.keyboard.release(key)
            except Exception:
                pass

    def stop(self):
        """停止监听器"""
        with self.lock:
            self.safe_release_keys()
            self.hotkey_listener.stop()
            print("\n🛑 热键监听已停止")

    def run(self):
        """启动监听"""
        print("🔥 热键监听已启动 (Alt+Shift+Q)")
        print("⏳ 现在可以选中文本后按热键读取")
        self.hotkey_listener.start()
        self.hotkey_listener.join()


if __name__ == "__main__":
    TextReader().run()
