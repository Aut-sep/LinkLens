# frontend/float_window.py

import sys
import subprocess
import os
from urllib.parse import quote_plus
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QColor


def show_floating(text=None):
    """
    每次都启动一个新的 Python 子进程去跑 float_window_app.py，
    这样里面的 QApplication 就一定在子进程的主线程中创建。
    """
    # 先处理空文本：如果 text 为空，则直接不弹出悬浮窗
    if not text:
        return

    # 1. 找到 float_window_app.py 的绝对路径
    this_dir = os.path.dirname(os.path.abspath(__file__))
    launcher = os.path.join(this_dir, "float_window_app.py")

    # 2. 对文本做 URL encode，防止空格和特殊字符导致命令行拆分
    param = quote_plus(text)

    # 3. 用 sys.executable 保证当前 Python 解释器（如果你 activate 了 conda/env）
    #    Popen 时不要 wait，直接异步弹出
    try:
        subprocess.Popen([sys.executable, launcher, param])
    except Exception as e:
        print(f"❌ 无法启动悬浮窗进程: {e}")


class FloatingWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(
            parent, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # 设置最小尺寸
        self.setMinimumSize(500, 100)
        self.setMaximumSize(500, 800)  # 限制最大高度

        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)

        # 创建标题栏
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(30)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)

        # 标题标签
        self.title_label = QLabel("LinkLens")
        self.title_label.setStyleSheet(
            """
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
            }
        """
        )

        # 关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet(
            """
            QPushButton {
                color: #FFFFFF;
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF0000;
                border-radius: 10px;
            }
        """
        )
        self.close_button.clicked.connect(self.close)

        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.close_button)

        # 创建内容区域
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(5)

        # 添加标题栏和内容区域到主布局
        self.main_layout.addWidget(self.title_bar)
        self.main_layout.addWidget(self.content)

        # 设置样式
        self.setStyleSheet(
            """
            QWidget {
                background-color: rgba(45, 45, 45, 0.95);
                border: 1px solid #666666;
                border-radius: 10px;
            }
        """
        )

        # 初始化拖动相关变量
        self.dragging = False
        self.drag_position = None

        # 设置窗口位置
        self.move_to_corner()

        # 添加阴影效果
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)

        # 设置窗口标志
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )

        # 设置窗口属性
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # 设置窗口大小策略
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        # 初始化内容
        self.clear_content()

        # 显示窗口
        self.show()

        # 设置定时器，5秒后自动关闭
        QTimer.singleShot(5000, self.close)

        # 加载设置
        self.settings = Settings()
        self.wait_content = self.settings.get("wait_content", False)
        self.content_loaded = False

    def move_to_corner(self):
        """将窗口移动到屏幕右上角"""
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, 20)

    def clear_content(self):
        """清空内容区域"""
        # 清除所有现有内容
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加加载提示
        loading_label = QLabel("加载中...")
        loading_label.setStyleSheet(
            """
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                padding: 10px;
            }
        """
        )
        loading_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(loading_label)

    def update_content(self, content: str):
        """更新内容区域"""
        self.clear_content()

        # 创建文本显示区域
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet(
            """
            QTextEdit {
                color: #FFFFFF;
                background-color: transparent;
                border: none;
                font-size: 14px;
                padding: 10px;
            }
        """
        )
        text_edit.setPlainText(content)

        # 设置文本编辑器的最大高度
        text_edit.setMaximumHeight(600)

        # 添加到布局
        self.content_layout.addWidget(text_edit)

        # 调整窗口大小以适应内容
        self.adjustSize()

        # 确保窗口不会超出屏幕
        screen = QApplication.primaryScreen().geometry()
        if self.height() > screen.height() - 40:
            self.setFixedHeight(screen.height() - 40)

        # 重新定位窗口
        self.move_to_corner()

        # 标记内容已加载完成
        self.content_loaded = True

    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 如果启用了等待内容加载完成，且内容未加载完成，则阻止关闭
        if self.wait_content and not self.content_loaded:
            event.ignore()
            return

        # 清理资源
        self.clear_content()
        event.accept()
