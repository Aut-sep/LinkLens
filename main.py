import threading
import time
from backend.mouse_read import TextReader
from backend.jina_read import JinaReader
from backend.summary_bot import SummaryBot

class MainProcessor:
    def __init__(self):
        print("🔄 初始化MainProcessor...")
        self.text_reader = TextReader()
        print("✅ TextReader初始化完成")
        self.jina_reader = JinaReader()
        print("✅ JinaReader初始化完成")
        self.summary_bot = SummaryBot()
        print("✅ SummaryBot初始化完成")
        self.lock = threading.Lock()
        print("🔒 线程锁已创建")

    def process_url(self, url):
        """处理URL的完整流程"""
        with self.lock:
            print(f"🔗 开始处理URL: {url}")
            
            # 获取Jina内容
            content = self.jina_reader.get_content(url)
            if not content:
                print("⚠️ 从Jina获取内容失败")
                return
                
            # 获取摘要
            summary = self.summary_bot.get_summary(url)
            if summary:
                print(f"📝 摘要生成成功:\n{summary}")
            else:
                print("⚠️ 摘要生成失败")

    def run(self):
        """启动主处理流程"""
        print("🔍 检查模块初始化状态...")
        print(f"📌 TextReader状态: {'正常' if hasattr(self.text_reader, 'hotkey_listener') else '异常'}")
        print(f"📌 JinaReader状态: {'正常' if hasattr(self.jina_reader, 'get_content') else '异常'}")
        print(f"📌 SummaryBot状态: {'正常' if hasattr(self.summary_bot, 'get_summary') else '异常'}")
        
        def on_text_selected(text):
            print(f"\n📥 接收到文本: {text}")
            if hasattr(self.text_reader, 'hotkey_listener') and self.text_reader.hotkey_listener.is_alive():
                if self.text_reader._is_url(text):
                    print("🔗 检测到有效URL，开始处理...")
                    self.process_url(text)
                else:
                    print(f"❌ 不是有效的URL: {text}")
            else:
                print("⚠️ 热键监听器未启动或已停止，请先确保热键监听器正常运行")
        
        # 修改TextReader的回调
        original_read = self.text_reader.read_selected_text
        self.text_reader.read_selected_text = lambda print_result=False: on_text_selected(original_read(print_result))
        
        print("🚀 系统已启动，请使用Alt+Shift+Q触发读取")
        try:
            self.text_reader.hotkey_listener.start()
            print("🔥 热键监听器已成功启动")
            # 保持主线程运行
            while True:
                time.sleep(1)
        except Exception as e:
            print(f"⚠️ 热键监听器启动失败: {e}")

if __name__ == "__main__":
    processor = MainProcessor()
    processor.run()