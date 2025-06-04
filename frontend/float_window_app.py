# frontend\float_window_app.py

import sys
import os
import tempfile
from PyQt5 import QtWidgets, QtCore, QtGui
from urllib.parse import unquote_plus


class FloatingWindow(QtWidgets.QWidget):
    def __init__(self, raw_arg=None):
        # 去掉标题栏、置顶、允许透明背景
        flags = QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint
        super().__init__(flags=flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)

        # 用于储存初始窗口位置，以便后续显示摘要时保持位置一致
        self.initial_pos = None

        self._timer = None  # 轮询线程用的定时器

        # ---------- 构造 UI ----------
        container = QtWidgets.QWidget(self)
        container.setObjectName("container")
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)

        self.label = QtWidgets.QLabel("")
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color: white; font-size: 12pt;")
        # 让标签随内容扩展
        self.label.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
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
        # --------------------------------

        # 根据传入参数决定是“加载中…”还是直接显示
        self._handle_arg(raw_arg)

        # 第一次根据标签内容自动调整尺寸
        self.adjustSize()

    def _handle_arg(self, raw_arg):
        """
        如果 raw_arg 以 "LOADING::" 开头，就进入“加载中…”模式并启动定时轮询。
        否则直接把 raw_arg 解码后显示（不截断长文本）。
        """
        if raw_arg and raw_arg.startswith("LOADING::"):
            parts = raw_arg.split("::", 1)
            if len(parts) == 2:
                uuid_str = parts[1]
                tmp_path = os.path.join(tempfile.gettempdir(), f"float_{uuid_str}.txt")
                # 先把标签设为“加载中…”
                self.label.setText("加载中…")
                # 构造轮询定时器：每300ms去检查 tmp_path
                self._timer = QtCore.QTimer(self)
                self._timer.setInterval(300)
                self._timer.timeout.connect(lambda: self._check_temp_file(tmp_path))
                self._timer.start()
            else:
                # 格式异常，直接解码显示
                self.label.setText(unquote_plus(raw_arg))
        else:
            # 普通模式，直接解码显示完整文本
            self.label.setText(unquote_plus(raw_arg or ""))

    def _check_temp_file(self, tmp_path):
        """
        定时轮询：如果发现 tmp_path 有非空内容，就把 label 换成摘要，
        然后手动计算高度，调用 resize(400, height)，最后 move(pos)。
        """
        try:
            if os.path.exists(tmp_path):
                with open(tmp_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    # ——（1）先把文本更新到 QLabel —— 
                    self.label.setText(content)

                    # ——（2）停止定时器 —— 
                    if self._timer:
                        self._timer.stop()
                        self._timer = None

                    # ——（3）删除临时文件（可选）—— 
                    try:
                        os.remove(tmp_path)
                    except:
                        pass

                    # ——（4）彻底清除“最小尺寸/最小高度”约束 —— 
                    #      让Windows/Qt 不要再把窗口强制撑到 243px 以上
                    self.setMinimumSize(0, 0)
                    self.setMinimumHeight(0)
                    self.setMaximumHeight(16777215)

                    # ——（5）锁定固定宽度 —— 
                    fixed_w = 400
                    self.setFixedWidth(fixed_w)

                    # ——（6）手动计算“内容+padding”后的高度 —— 

                    # 6.1 先让 label 固定一个宽度：400 减去左右各15的 padding（container_layout 中设置的 margins）
                    label_target_width = fixed_w - 15 * 2
                    self.label.setFixedWidth(label_target_width)

                    # 6.2 调用 label.adjustSize()，让它自己根据内容算出高度
                    self.label.adjustSize()
                    label_h = self.label.height()

                    # 6.3 container 的上下也各 15px，所以总高度 = label_h + 15*2
                    total_h = label_h + 15 * 2

                    # ——（7）调用 resize，将整个浮窗设置为 400×total_h —— 
                    #      Windows 会检查“我们要的高度是不是 >= 最小跟踪高度”，
                    #      只要 total_h 稍微大于实际的文字所需高度，肯定可以 pass。
                    self.resize(fixed_w, total_h)

                    # ——（8）最后做边界检查并 move —— 
                    x = self.initial_pos.x()
                    y = self.initial_pos.y()
                    screen = QtWidgets.QApplication.screenAt(self.initial_pos)
                    if screen:
                        geo = screen.availableGeometry()
                        # 右边越界就往左移
                        if x + fixed_w + 5 > geo.right():
                            x = geo.right() - fixed_w - 5
                        # 下边越界就往上移
                        if y + total_h + 5 > geo.bottom():
                            y = geo.bottom() - total_h - 5
                        # 不要贴屏幕左/上缘
                        if x < geo.left() + 5:
                            x = geo.left() + 5
                        if y < geo.top() + 5:
                            y = geo.top() + 5

                    self.move(x, y)

        except Exception:
            # 如果读文件或计算大小时挂了，下次定时器继续尝试
            pass

    def showEvent(self, event: QtGui.QShowEvent):
        super().showEvent(event)
        # 保证窗口展示时立刻获得焦点
        self.activateWindow()
        self.setFocus(QtCore.Qt.MouseFocusReason)
        # 在首次 show 时记录初始位置
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
        if getattr(self, "_drag_active", False) and (
            event.buttons() & QtCore.Qt.LeftButton
        ):
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
        text = unquote_plus(sys.argv[1])

    app = QtWidgets.QApplication(sys.argv)
    win = FloatingWindow(text)

    # 初次弹出时，先调整尺寸，再定位
    win.show()
    win.adjustSize()  # 保证第一次根据“加载中...”文本调整大小

    w = win.width()
    h = win.height()
    cursor_point = QtGui.QCursor.pos()
    target_x = cursor_point.x()
    target_y = cursor_point.y()
    screen = QtWidgets.QApplication.screenAt(cursor_point)
    screen_geo = screen.availableGeometry()
    screen_w = screen_geo.width()
    screen_h = screen_geo.height()

    x = screen_w - w - 20
    y = screen_h - h - 50

    if target_x is not None and target_y is not None:
        offset = 12
        x = target_x + offset
        y = target_y + offset

        if target_y + offset + h > screen_h:
            y = target_y - offset - h
            if y < 5:
                y = 5

        if x + w + 5 > screen_w:
            x = screen_w - w - 5
        if y + h + 5 > screen_h:
            y = screen_h - h - 5

    win.move(x, y)
    # 在首次定位后记录位置
    win.initial_pos = win.pos()

    win.raise_()
    win.activateWindow()
    app.exec_()
