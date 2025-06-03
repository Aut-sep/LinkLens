# frontend/float_window_app.py

import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from urllib.parse import unquote_plus


class FloatingWindow(QtWidgets.QWidget):
    def __init__(self, text=None):
        # 使用 FramelessWindowHint 去掉标题栏，并保持在工具层级
        flags = QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint
        super().__init__(flags=flags)

        # 让窗口拥有透明背景，圆角部分自己在子 widget 里画
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # 确保点击时此窗口可以获得焦点
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        # 保持窗口总在最前（可选，根据需要）
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)

        # 用于记录拖拽状态
        self._drag_active = False
        self._drag_start_pos = None

        # 外层 container，用来做半透明圆角黑底
        container = QtWidgets.QWidget(self)
        container.setObjectName("container")
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)

        # 标签用于显示摘要文字
        label = QtWidgets.QLabel(unquote_plus(text or ""))
        label.setWordWrap(True)
        label.setStyleSheet("color: white; font-size: 12pt;")
        container_layout.addWidget(label)

        # 设置半透明黑底 + 圆角
        container.setStyleSheet(
            """
            QWidget#container {
                background: rgba(0, 0, 0, 0.7);
                border-radius: 12px;
            }
            """
        )

        # 最外层布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        # 根据文字内容让窗口自适应大小
        self.adjustSize()

    def showEvent(self, event: QtGui.QShowEvent):
        """
        窗口刚刚显示时，让它获得焦点，以便后续点击外部能触发 focusOutEvent。
        """
        super().showEvent(event)
        # 激活并聚焦此窗口
        self.activateWindow()
        self.setFocus(QtCore.Qt.MouseFocusReason)

    def focusOutEvent(self, event: QtGui.QFocusEvent):
        """
        当窗口失去焦点时（即用户点击了外部或切到别的窗口），直接关闭自己。
        """
        self.close()
        super().focusOutEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """
        左键按下时开始拖拽：记录鼠标相对于窗口左上角的偏移。
        """
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_active = True
            self._drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        """
        鼠标移动且左键仍在按下，则计算新的窗口位置并移动。
        """
        if self._drag_active and (event.buttons() & QtCore.Qt.LeftButton):
            new_pos = event.globalPos() - self._drag_start_pos
            self.move(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        """
        左键松开，结束拖拽状态。
        """
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_active = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)


if __name__ == "__main__":
    # 测试用：从命令行参数取文本并显示
    text = ""
    if len(sys.argv) > 1:
        text = unquote_plus(sys.argv[1])
    app = QtWidgets.QApplication(sys.argv)
    win = FloatingWindow(text)

    # 将浮窗定位到右下角（根据屏幕可用区域自动调整）
    screen_geo = QtWidgets.QApplication.primaryScreen().availableGeometry()
    x = screen_geo.width() - win.width() - 20
    y = screen_geo.height() - win.height() - 50
    win.move(x, y)

    win.show()
    app.exec_()
