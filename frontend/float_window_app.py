# frontend/float_window_app.py

import sys
import os
import tempfile
import json
from PyQt5 import QtWidgets, QtCore, QtGui
from urllib.parse import unquote_plus

# 配置文件路径应与 settings.py 保持一致
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".linklens", "config.json")


class FloatingWindow(QtWidgets.QWidget):
    def __init__(self, raw_arg=None):
        # 解码参数
        decoded_arg = unquote_plus(raw_arg or "")

        # 如果是空字符串，则退出
        if not decoded_arg:
            QtWidgets.QApplication.quit()
            return

        # 判断是否是“示例预览模式”
        is_preview = False
        preview_text = ""
        if decoded_arg.startswith("PREVIEW::"):
            is_preview = True
            preview_text = decoded_arg.split("::", 1)[1]

        # —— 通用窗口属性：去掉标题栏、置顶、允许透明背景 —— #
        flags = QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint
        super().__init__(flags=flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)

        self.initial_pos = None
        self._timer = None

        # ---------- 构造 UI ---------- #
        container = QtWidgets.QWidget(self)
        container.setObjectName("container")
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)

        self.label = QtWidgets.QLabel("")
        self.label.setWordWrap(True)
        # 样式暂时留空，后面根据配置替换
        container_layout.addWidget(self.label)

        container.setStyleSheet(
            """
            QWidget#container {
                background: rgba(0, 0, 0, 0.7);
                border-radius: 12px;
            }
            """
        )

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        # 如果是“示例预览”模式
        if is_preview:
            self._apply_style_and_show(preview_text)
            return  # 不进入“LOADING::”或轮询逻辑

        # —— 否则，和原先代码保持一致：判断是 LOADING:: 还是 直接显示 —— #
        self._handle_arg(raw_arg)

        # 第一次根据标签内容自动调整尺寸
        self.adjustSize()

    def _apply_style_and_show(self, text: str):
        """
        专用于“PREVIEW::”模式：
        1) 从配置文件里读取字体/颜色/不透明度
        2) 应用到 QLabel 和窗口
        3) 直接 show() 并在屏幕右下角弹出示例
        """
        # 1. 读取当前配置
        font_family = "Sans Serif"
        font_size = 12
        font_color = "#FFFFFF"
        window_opacity = 0.8

        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    font_family = cfg.get("font_family", font_family)
                    font_size = cfg.get("font_size", font_size)
                    font_color = cfg.get("font_color", font_color)
                    window_opacity = cfg.get("window_opacity", window_opacity)
        except:
            pass  # 如有任何错误，用默认

        # 2. 设置标签文字与样式
        self.label.setText(text)
        font = QtGui.QFont(font_family, font_size)
        self.label.setFont(font)
        # 字体颜色
        self.label.setStyleSheet(f"color: {font_color};")

        # 3. 调整窗口整体不透明度
        self.setWindowOpacity(window_opacity)

        # 4. 调整大小后再定位到屏幕右下或鼠标附近
        self.adjustSize()
        w = self.width()
        h = self.height()
        cursor_point = QtGui.QCursor.pos()
        screen = QtWidgets.QApplication.screenAt(cursor_point)
        if screen:
            geo = screen.availableGeometry()
            # 尽量出现在鼠标偏右下方，若越界则调整
            offset = 12
            x = cursor_point.x() + offset
            y = cursor_point.y() + offset
            if x + w + 5 > geo.right():
                x = geo.right() - w - 5
            if y + h + 5 > geo.bottom():
                y = cursor_point.y() - offset - h
                if y < geo.top() + 5:
                    y = geo.top() + 5
            if x < geo.left() + 5:
                x = geo.left() + 5
            if y < geo.top() + 5:
                y = geo.top() + 5
            self.move(x, y)

        self.show()
        self.raise_()
        self.activateWindow()

    def _handle_arg(self, raw_arg):
        """
        如果 raw_arg 以 "LOADING::" 开头，就进入“加载中…”模式并启动轮询。
        否则直接解码后显示完整文本。
        """
        decoded_arg = unquote_plus(raw_arg or "")
        if raw_arg and raw_arg.startswith("LOADING::"):
            parts = raw_arg.split("::", 1)
            if len(parts) == 2:
                uuid_str = parts[1]
                tmp_path = os.path.join(tempfile.gettempdir(), f"float_{uuid_str}.txt")
                self.label.setText("加载中…")
                # 轮询定时器
                self._timer = QtCore.QTimer(self)
                self._timer.setInterval(300)
                self._timer.timeout.connect(lambda: self._check_temp_file(tmp_path))
                self._timer.start()
            else:
                # 格式异常，直接当普通显示
                self.label.setText(decoded_arg)
        else:
            # 普通模式，直接显示
            self.label.setText(decoded_arg)

    def _check_temp_file(self, tmp_path):
        """
        “加载中…”时定时轮询 tmp_path，如果文件内容有了，就更新 label 并调整大小、定位。
        """
        try:
            if os.path.exists(tmp_path):
                with open(tmp_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    # 更新文字
                    self.label.setText(content)
                    # 停止轮询
                    if self._timer:
                        self._timer.stop()
                        self._timer = None
                    # 删除临时文件
                    try:
                        os.remove(tmp_path)
                    except:
                        pass

                    # 清除最小尺寸约束
                    self.setMinimumSize(0, 0)
                    self.setMinimumHeight(0)
                    self.setMaximumHeight(16777215)

                    # 固定宽度 500 px
                    fixed_w = 500
                    self.setFixedWidth(fixed_w)

                    # 计算内容高度
                    label_target_width = fixed_w - 15 * 2
                    self.label.setFixedWidth(label_target_width)
                    self.label.adjustSize()
                    label_h = self.label.height()
                    total_h = label_h + 15 * 2
                    self.resize(fixed_w, total_h)

                    # 最后做边界检查并 move
                    x = self.initial_pos.x()
                    y = self.initial_pos.y()
                    screen = QtWidgets.QApplication.screenAt(self.initial_pos)
                    if screen:
                        geo = screen.availableGeometry()
                        if x + fixed_w + 5 > geo.right():
                            x = geo.right() - fixed_w - 5
                        if y + total_h + 5 > geo.bottom():
                            y = geo.bottom() - total_h - 5
                        if x < geo.left() + 5:
                            x = geo.left() + 5
                        if y < geo.top() + 5:
                            y = geo.top() + 5
                    self.move(x, y)

        except Exception:
            pass  # 出错也不影响后续轮询

    def showEvent(self, event: QtGui.QShowEvent):
        super().showEvent(event)
        self.activateWindow()
        self.setFocus(QtCore.Qt.MouseFocusReason)
        if self.initial_pos is None:
            self.initial_pos = self.pos()

    def focusOutEvent(self, event: QtGui.QFocusEvent):
        # 失去焦点就自动关闭
        self.close()
        super().focusOutEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_active = True
            self._drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if getattr(self, "_drag_active", False) and (event.buttons() & QtCore.Qt.LeftButton):
            new_pos = event.globalPos() - self._drag_start_pos
            self.move(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_active = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)


if __name__ == "__main__":
    text = ""
    if len(sys.argv) > 1:
        text = unquote_plus(sys.argv[1] or "")
    if not text:
        sys.exit(0)

    app = QtWidgets.QApplication(sys.argv)
    win = FloatingWindow(text)
    if not isinstance(win, FloatingWindow):
        sys.exit(0)
    win.show()
    win.adjustSize()

    # 定位逻辑与普通情况一致(不再赘述)
    w = win.width()
    h = win.height()
    cursor_point = QtGui.QCursor.pos()
    screen = QtWidgets.QApplication.screenAt(cursor_point)
    screen_geo = screen.availableGeometry()
    screen_w = screen_geo.width()
    screen_h = screen_geo.height()

    x = cursor_point.x() + 12
    y = cursor_point.y() + 12
    if x + w + 5 > screen_w:
        x = cursor_point.x() - 12 - w
        if x < 5:
            x = 5
    if y + h + 5 > screen_h:
        y = cursor_point.y() - 12 - h
        if y < 5:
            y = 5
    if x < 5:
        x = 5
    if y < 5:
        y = 5

    win.move(x, y)
    win.initial_pos = win.pos()

    win.raise_()
    win.activateWindow()
    app.exec_()
