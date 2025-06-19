# main.py

import threading
import time
import traceback
import sys
import os
import uuid
import tempfile

from backend.mouse_read import TextReader
from backend.summary_bot import SummaryBot
from backend.jina_read import JinaReader
from backend.pic import ImageExtractor
from backend.video import AudioExtractor
from backend.speech_to_text import XunfeiSpeechRecognizer
from frontend.float_window import show_floating
from PyQt5 import QtWidgets, QtCore
from frontend.config_window import ConfigWindow
from pynput import keyboard
from settings import Settings


class MainProcessor(QtCore.QObject):
    """
    这里把 MainProcessor 改为 QObject，方便接收 ConfigWindow.hotkeyChanged 信号。
    """

    def __init__(self):
        super().__init__()
        print("🔄 初始化 MainProcessor...")
        self.settings = Settings()
        self.debug = self.settings.get("debug", False)
        if self.debug:
            print("🔧 Debug模式已启用")
        self.text_reader = TextReader()
        print("✅ TextReader 初始化完成")
        self.summary_bot = SummaryBot(settings=self.settings)
        self.summary_bot.debug = self.debug
        print("✅ SummaryBot 初始化完成")
        self.jina_reader = JinaReader()
        print("✅ JinaReader 初始化完成")
        self.image_extractor = ImageExtractor()
        self.image_extractor.debug = self.debug
        print("✅ ImageExtractor 初始化完成")
        self.audio_extractor = AudioExtractor()
        self.audio_extractor.debug = self.debug
        print("✅ AudioExtractor 初始化完成")
        self.speech_recognizer = XunfeiSpeechRecognizer(settings=self.settings)
        print("✅ SpeechRecognizer 初始化完成")
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
        self.hotkey_listener = keyboard.GlobalHotKeys(
            {pynput_str: self._trigger_and_summarize}
        )
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
            "Meta": "cmd",
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

                # 获取并处理网页内容
                if self.debug:
                    print("🔧 Debug模式：使用模拟网页内容")
                    web_summary = self.summary_bot.auto_summarize("", "网页内容")
                    summary = web_summary
                else:
                    if content := self.jina_reader.get_content(text):
                        print("✅ 网页内容获取成功")
                        if web_summary := self.summary_bot.auto_summarize(
                            content, "网页内容"
                        ):
                            print(f"📝 网页内容总结:\n{web_summary}")
                            summary = web_summary
                        else:
                            summary = "❌ 无法生成网页内容总结"
                    else:
                        summary = "❌ 无法获取网页内容"

                # 如果启用了图片提取
                if self.settings.get("extract_image", True):
                    images = self.image_extractor.get_image_summary(text)
                    if images:
                        print(f"🖼️ 找到 {len(images)} 张图片")
                        for img_url in images:
                            summary += f"\n{img_url}"
                    else:
                        print("❌ 未找到符合要求的图片")

                # 如果启用了音频内容总结
                if self.settings.get("summarize_audio", True):
                    audio_path = None
                    try:
                        print("\n🎵 开始处理音频内容...")
                        print("📥 正在从URL提取音频...")
                        if self.debug:
                            print("🔧 Debug模式：使用模拟音频内容")
                            audio_path = self.audio_extractor.extract_audio(text)
                            text_result = (
                                "这是模拟的语音识别结果，用于测试音频内容总结功能。"
                            )
                            audio_summary = self.summary_bot.auto_summarize(
                                text_result, "音频内容"
                            )
                            summary += f"\n\n音频内容总结:\n{audio_summary}"
                        else:
                            if not (
                                audio_path := self.audio_extractor.extract_audio(text)
                            ):
                                print("❌ 音频提取失败")
                            else:
                                print(f"✅ 音频提取成功！文件路径：{audio_path}")

                                print("\n🗣️ 开始语音识别...")
                                if text_result := self.speech_recognizer.transcribe(
                                    audio_path
                                ):
                                    print(f"✅ 语音识别完成！识别结果：\n{text_result}")

                                    print("\n📝 开始总结音频内容...")
                                    if audio_summary := self.summary_bot.auto_summarize(
                                        text_result, "音频内容"
                                    ):
                                        print(f"✅ 音频内容总结完成！\n{audio_summary}")
                                        summary += f"\n\n音频内容总结:\n{audio_summary}"
                                    else:
                                        print("❌ 音频内容总结失败")
                                else:
                                    print("❌ 语音识别失败")

                    except Exception as e:
                        print(
                            "❌ 音频处理失败: "
                            + (
                                "链接不受支持"
                                if "Unsupported URL" in str(e)
                                else str(e)
                            )
                        )

                    finally:
                        if audio_path and not self.debug:
                            print("\n🧹 清理临时文件...")
                            self.audio_extractor.delete_file(audio_path)
                            print("✅ 临时文件清理完成")
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

        uuid_str = str(uuid.uuid4())
        tmp_path = os.path.join(tempfile.gettempdir(), f"float_{uuid_str}.txt")
        try:
            with open(tmp_path, "w", encoding="utf-8"):
                pass
        except Exception as e:
            print(f"❌ 无法创建临时文件 {tmp_path}：{e}")
            return

        print(f'🌀 弹出"加载中..."悬浮窗，UUID={uuid_str}')
        show_floating(f"LOADING::{uuid_str}")

        worker = threading.Thread(
            target=self._process_text_and_write, args=(text, tmp_path), daemon=True
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
        mapping_inv = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift", "cmd": "Meta"}
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

    # 连接调试模式变更信号
    def on_debug_changed(debug_enabled: bool):
        processor.debug = debug_enabled
        # 更新各个模块的 debug 属性
        processor.summary_bot.debug = debug_enabled
        processor.image_extractor.debug = debug_enabled
        processor.audio_extractor.debug = debug_enabled
        print(f"{'🔧 Debug模式已启用' if debug_enabled else '🔧 Debug模式已禁用'}")

    config_win.debugChanged.connect(on_debug_changed)

    # —— 4. 后台线程运行 processor.run() —— #
    threading.Thread(target=processor.run, daemon=True).start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
