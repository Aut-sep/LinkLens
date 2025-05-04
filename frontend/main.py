import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer
from floating import FloatingWindow

class LinkLensApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = FloatingWindow()
        
        # 模拟AI处理流程
        self.window.show_loading()
        self.window.fade_in()
        self.window.move(100, 100)  # 初始位置
        
        # 模拟2秒后收到AI结果
        QTimer.singleShot(2000, self.demo_update_content)

    def demo_update_content(self):
        # 示例数据
        summary = "这是一篇关于量子计算的科普文章，主要讲述了：\n\n"
        summary += "• 量子比特与传统二进制位的区别\n"
        summary += "• 量子纠缠在通信中的潜在应用\n"
        summary += "• 当前量子计算机的发展瓶颈"
        
        image_path = "assets/sample_image.jpg"  # 测试图片路径
        
        self.window.show_content(summary, image_path)

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    LinkLensApp().run()