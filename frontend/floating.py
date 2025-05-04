from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, pyqtProperty
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPixmap, QMovie, QFont, QColor, QPainter, QPen
from PyQt5 import QtCore

class FloatingWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_style()
        self.drag_pos = QPoint()

    def setup_ui(self):
        # 窗口基础设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(300, 200)
        
        # 主布局
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        # 标题栏
        self.title_bar = QWidget()
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel("LinkLens Preview")
        self.title_label.setFixedHeight(20)
        
        self.close_btn = QLabel("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.mousePressEvent = lambda _: self.hide()
        
        title_layout.addWidget(self.title_label)
        title_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding))
        title_layout.addWidget(self.close_btn)
        self.title_bar.setLayout(title_layout)

        # 加载动画
        self.loading_movie = QMovie("assets/loading.gif")  # 准备一个加载动画GIF
        self.loading_label = QLabel()
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.hide()

        # 内容区域
        self.content_area = QVBoxLayout()
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignTop)
        
        self.image_container = QLabel()
        self.image_container.setAlignment(Qt.AlignCenter)
        self.image_container.setFixedSize(280, 150)  # 限制图片显示尺寸
        
        self.content_area.addWidget(self.summary_label)
        self.content_area.addWidget(self.image_container)

        # 组合布局
        self.layout.addWidget(self.title_bar)
        self.layout.addWidget(self.loading_label)
        self.layout.addLayout(self.content_area)
        self.setLayout(self.layout)

    def setup_style(self):
        # 从CSS文件加载样式
        with open("frontend/styles.css", "r") as f:
            self.setStyleSheet(f.read())

    def paintEvent(self, event):
        # 绘制圆角和阴影
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制阴影
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 30))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 8, 8)
        
        # 绘制背景
        painter.setBrush(QColor(255, 255, 255))
        painter.setPenQPen(QColor(220, 220, 220), 1)
        painter.drawRoundedRect(2, 2, self.width()-4, self.height()-4, 6, 6)

    # 鼠标拖动相关事件
    def mousePressEvent(self, event):
        self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)

    # 公有方法
    def show_loading(self):
        """显示加载动画"""
        self.content_area.setEnabled(False)
        self.loading_label.show()
        self.loading_movie.start()

    def show_content(self, summary: str, image_path: str = None):
        """更新展示内容"""
        self.loading_movie.stop()
        self.loading_label.hide()
        self.content_area.setEnabled(True)
        
        self.summary_label.setText(summary)
        if image_path:
            pixmap = QPixmap(image_path)
            self.image_container.setPixmap(pixmap.scaled(
                self.image_container.size(), 
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        else:
            self.image_container.clear()

    def fade_in(self):
        """渐入动画"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()