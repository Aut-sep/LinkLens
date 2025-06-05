# main.py

import threading
import time
import os
import uuid
import tempfile
import traceback
from backend.mouse_read import TextReader
from backend.summary_bot import SummaryBot
from frontend.float_window import show_floating

# 额外导入，用来重新创建热键监听器
from pynput import keyboard  


class MainProcessor:
    def __init__(self):
        print("🔄 初始化MainProcessor...")
        self.text_reader = TextReader()
        print("✅ TextReader初始化完成")
        self.summary_bot = SummaryBot()
        print("✅ SummaryBot初始化完成")
        self.lock = threading.Lock()
        print("🔒 线程锁已创建")

        # 保存原始的 “只读取剪贴板并打印调试” 方法
        self._original_read = self.text_reader.read_selected_text

        # --------------- 关键修改：重新创建 HotKeys 监听器 ---------------
        # 不再使用 text_reader.__init__ 中那个早先创建的 hotkey_listener，
        # 而是用新的 mapping 把 <alt>+<shift>+q 直接指向 _trigger_and_summarize
        self.text_reader.hotkey_listener = keyboard.GlobalHotKeys(
            {
                "<alt>+<shift>+q": self._trigger_and_summarize,
                "<alt>+<shift>+w": self.text_reader.stop,
            }
        )
        # ------------------------------------------------------------------

    def _process_text_and_write(self, text: str, tmp_path: str):
        """后台线程：判断 URL 并写摘要到 tmp_path。"""
        if not text:
            summary = "\n⚠️ 没有读取到文本"
        else:
            print(f"📥 文本: {repr(text)}")
            if self.text_reader._is_url(text):
                print("🔗 检测到有效URL，开始处理...")
                summary = self.summary_bot.get_summary(text)
                if summary:
                    print(f"📝 摘要生成成功")
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
        """
        热键按下时执行：
        1. 先调用原来的 read_selected_text 拿到剪贴板文本并打印 
        2. 生成一个临时文件 tmp_path，用于“主进程 -> 悬浮窗”的通信
        3. 立刻弹出一个悬浮窗，内容为“加载中…”，并把 uuid 传给前端
        4. 在后台线程里拿到摘要并写回 tmp_path，前端检测到后更新显示
        """
        # —— 1. 先读剪贴板、打印调试 —— 
        text = ""
        try:
            text = self._original_read(print_result=True)  # 如果 read_selected_text 抛异常，这里捕获
        except Exception as e:
            print(f"❌ 读取剪贴板时出错: {e}")
            text = ""

        # —— 2. 生成 UUID，并建立对应的空文件 —— 
        uuid_str = str(uuid.uuid4())
        tmp_path = os.path.join(tempfile.gettempdir(), f"float_{uuid_str}.txt")
        try:
            with open(tmp_path, "w", encoding="utf-8"):
                pass
        except Exception as e:
            print(f"❌ 无法创建临时文件 {tmp_path}：{e}")
            return

        # —— 3. 立刻弹出“加载中…”悬浮窗 —— 
        print(f"🌀 正在弹出“加载中…”悬浮窗，UUID={uuid_str}")
        show_floating(f"LOADING::{uuid_str}")

        # —— 4. 后台线程去抓取摘要并写回 tmp_path —— 
        worker = threading.Thread(
            target=self._process_text_and_write, 
            args=(text, tmp_path),
            daemon=True
        )
        worker.start()

    def run(self):
        """启动监听。"""
        print("🔍 检查模块初始化状态...")
        if not hasattr(self.text_reader, "read_selected_text"):
            print("⚠️ TextReader 缺少 read_selected_text")
        if not hasattr(self.summary_bot, "get_summary"):
            print("⚠️ SummaryBot 缺少 get_summary")

        print("🚀 系统启动完成，按 Alt+Shift+Q 触发")
        try:
            # 这里启动的是我们新建的 hotkey_listener，而非 TextReader 内部初始化的那个
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
            print(f"⚠️ 热键监听器启动或运行时发生异常: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    # 我们让最外层再包一层 try/except，一旦发生未捕获异常，就打印日志并重启 main().
    def _main_loop():
        try:
            processor = MainProcessor()
            # debug 模式，绕过summary_bot：
            processor.summary_bot.debug = True
            processor.run()
        except Exception as e:
            print("❌ 主进程发生未捕获异常，稍后重新启动：")
            traceback.print_exc()
            time.sleep(1)
            _main_loop()

    _main_loop()
