# backend/mouse_read.py

import time
import re
import pyperclip
from frontend.float_window import show_floating
from pynput import keyboard
from pynput import mouse
from urllib.parse import urlparse
from threading import Lock
import uuid


class TextReader:
    def __init__(self):
        self.lock = Lock()
        self.keyboard = keyboard.Controller()
        self.hotkey_listener = keyboard.GlobalHotKeys(
            {
                "<alt>+<shift>+q": self.trigger_read,
                "<alt>+<shift>+w": self.stop,
            }
        )
        # 标记：上一次成功读出的内容，用于去重
        self.last_fetched_text = None

    def trigger_read(self):
        """热键触发入口（增加异常保护，避免 read_selected_text 内部异常把整个线程打掉）"""
        with self.lock:
            try:
                text = self.read_selected_text()
            except Exception as e:
                # 即便 read_selected_text 报错，也不让整个监听退出
                print(f"❌ trigger_read 内部异常: {e}")
                return

            print(f"   — 读取到的文本: {repr(text)}")  # debug

            try:
                m = mouse.Controller()
                x, y = m.position
                print(f"   — 当前鼠标坐标: ({x}, {y})")
            except Exception as e:
                print(f"⚠️ 获取鼠标坐标失败: {e}")
                x, y = None, None

        # 无论 text 是空、URL 还是普通文本，都传给前端，由前端决定怎么处理
        show_floating(text)

    def _is_url(self, text):
        """URL 验证方法"""
        pattern = re.compile(
            r"^(?:http|ftp)s?://|^"
            r"(?:www\.)?"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        if not re.match(pattern, text):
            return False
        try:
            parsed = urlparse(text if "://" in text else f"http://{text}")
            return all([parsed.scheme, parsed.netloc]) and "." in parsed.netloc
        except:
            return False

    def read_selected_text(self, print_result=True):
        """
        防御性读取逻辑：
        1) 先读 original；
        2) 写入随机占位符（UUID）并确认刷新；
        3) 模拟 Ctrl+C，并轮询等待剪贴板脱离占位符；
        4) 判重：如果读到的内容 == 上次成功取到的文本，则视作“重复”，直接返回空；
        5) 判若内容正好等于 placeholder 或者为空，都认为“未正确复制”；
        6) 恢复原始剪贴板；返回 new_text（可能是空）。
        """
        try:
            # —— 步骤①：备份原剪贴板内容
            original = pyperclip.paste()
        except Exception as e:
            if print_result:
                print(f"❌ 无法读取剪贴板原始内容: {e}")
            original = ""

        # —— 步骤②：用 UUID 占位
        placeholder = str(uuid.uuid4())
        try:
            pyperclip.copy(placeholder)
        except Exception as e:
            if print_result:
                print(f"❌ 无法写入剪贴板占位符: {e}")
        # 确保剪贴板先刷新成 placeholder
        time.sleep(0.05)

        # 先释放残留按键
        self.safe_release_keys()

        # —— 步骤③：模拟 Ctrl+C
        self.keyboard.press(keyboard.Key.ctrl)
        self.keyboard.press("c")
        self.keyboard.release("c")
        self.keyboard.release(keyboard.Key.ctrl)

        # 轮询等待：直到剪贴板内容 != placeholder，或超时
        new_text = None
        max_wait = 1.0  # 最长等 1 秒，如果网络驱动剪贴板较慢，可适当调大
        interval = 0.05  # 每 50ms 检查一次
        elapsed = 0.0

        while elapsed < max_wait:
            try:
                current = pyperclip.paste()
            except Exception:
                current = None
            if current is None:
                # 如果暂时拿不到，短暂 sleep 然后再试
                time.sleep(interval)
                elapsed += interval
                continue

            # 一旦检测到剪贴板的内容不再是 placeholder，就取它
            if current != placeholder:
                new_text = current.strip()
                break

            time.sleep(interval)
            elapsed += interval

        # —— 步骤④：当 new_text 仍为 None，或 new_text == placeholder，或 new_text 为空时，都视为“未复制到有效文本”
        if not new_text or new_text == placeholder:
            if print_result:
                print("\n⚠️ 未获取到有效内容")
            # 恢复原剪贴板后直接返回空串
            try:
                pyperclip.copy(original)
            except Exception:
                pass
            return ""

        # # —— 步骤⑤：判重——如果与上次成功获取的文本一致，也认为“重复”，直接恢复原剪贴板并返回空
        # if new_text == self.last_fetched_text:
        #     if print_result:
        #         print("\n⚠️ 内容与上次相同，视作无效")
        #     try:
        #         pyperclip.copy(original)
        #     except Exception:
        #         pass
        #     return ""

        # —— 截至这里，new_text 是“有效且与上次不同”的文本
        self.last_fetched_text = new_text
        if print_result:
            print(f"\n📝 读取到: {new_text}")

        # —— 步骤⑥：恢复原剪贴板
        try:
            pyperclip.copy(original)
        except Exception:
            if print_result:
                print("⚠️ 恢复剪贴板原始内容失败")

        return new_text

    def safe_release_keys(self):
        """安全释放可能残留的按键"""
        for key in [keyboard.Key.ctrl, "c", keyboard.Key.alt, keyboard.Key.shift]:
            try:
                self.keyboard.release(key)
            except Exception:
                pass

    def stop(self):
        with self.lock:
            self.safe_release_keys()
            self.hotkey_listener.stop()
            print("\n🛑 热键监听已停止")

    def run(self):
        print("🔥 热键监听已启动 (Alt+Shift+Q)")
        print("⏳ 现在可以选中文本后按热键读取")
        self.hotkey_listener.start()
        self.hotkey_listener.join()


if __name__ == "__main__":
    TextReader().run()
