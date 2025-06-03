# main.py

import threading
import time
from backend.mouse_read import TextReader
from backend.summary_bot import SummaryBot


class MainProcessor:
    def __init__(self):
        print("🔄 初始化MainProcessor...")
        self.text_reader = TextReader()
        print("✅ TextReader初始化完成")
        self.summary_bot = SummaryBot()
        print("✅ SummaryBot初始化完成")
        self.lock = threading.Lock()
        print("🔒 线程锁已创建")

        self._original_trigger = self.text_reader.trigger_read
        self._original_read = self.text_reader.read_selected_text

        self.text_reader.trigger_read = self._trigger_and_summarize

    def _process_text(self, text: str):
        """判断 URL 并摘要，否则打印提示。"""
        if not text:
            print("\n📥 没有读取到文本")
            return

        print(f"\n📥 文本: {repr(text)}")
        if self.text_reader._is_url(text):
            print("🔗 检测到有效URL，开始处理...")
            with self.lock:
                print(f"🔗 开始处理URL: {text}")
                summary = self.summary_bot.get_summary(text)
                if summary:
                    print(f"📝 摘要生成成功:\n{summary}")
                else:
                    print("⚠️ 摘要生成失败")
        else:
            print(f"❌ 不是有效的URL: {repr(text)}")

    def _trigger_and_summarize(self):
        """先调用原 trigger，再拿文本摘要。"""
        self._original_trigger()
        text = self.text_reader.read_selected_text(print_result=False)
        self._process_text(text)

    def run(self):
        """启动监听，替换 read_selected_text，主线程保持运行。"""
        print("🔍 检查模块初始化状态...")
        if not hasattr(self.text_reader, "read_selected_text"):
            print("⚠️ TextReader 缺少 read_selected_text")
        if not hasattr(self.summary_bot, "get_summary"):
            print("⚠️ SummaryBot 缺少 get_summary")

        self.text_reader.read_selected_text = self._patched_read_selected_text

        print("🚀 系统启动完成，按 Alt+Shift+Q 触发")
        try:
            self.text_reader.hotkey_listener.start()
            print("🔥 热键监听器已成功启动")

            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            try:
                self.text_reader.stop()
            except Exception:
                pass
            print("🛑 程序由用户中断，正在退出...")

        except Exception as e:
            print(f"⚠️ 热键监听器启动失败: {e}")

    def _patched_read_selected_text(self, print_result=False) -> str:
        """调用原 read，直接摘要并返回文本。"""
        text = self._original_read(print_result)
        self._process_text(text)
        return text


if __name__ == "__main__":
    processor = MainProcessor()
    processor.summary_bot.debug = True
    processor.run()
