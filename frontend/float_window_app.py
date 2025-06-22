# frontend/float_window_app.py

import sys
import os
import tempfile
import json
import re
import requests
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

        # 判断是否是"示例预览模式"
        # 判断是否是"示例预览模式"
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

        # 创建图片显示区域
        self.image_widget = QtWidgets.QWidget()
        self.image_layout = QtWidgets.QHBoxLayout(self.image_widget)
        self.image_layout.setContentsMargins(0, 0, 0, 0)
        self.image_layout.setSpacing(10)
        container_layout.addWidget(self.image_widget)

        # 初始时隐藏图片区域
        self.image_widget.hide()
        self.label.show()  # 确保文本标签可见

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

        # 如果是"示例预览"模式
        # 如果是"示例预览"模式
        if is_preview:
            self._apply_style_and_show(preview_text)
            return  # 不进入"LOADING::"或轮询逻辑

        # —— 否则，和原先代码保持一致：判断是 LOADING:: 还是 直接显示 —— #
        self._handle_arg(raw_arg)

        # 第一次根据标签内容自动调整尺寸
        self.adjustSize()

    def _is_image_url(self, text):
        """检测文本是否为图片链接"""
        # 图片文件扩展名
        image_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
            ".svg",
            ".ico",
        ]

        # 更宽松的图片URL模式，包括可能的重定向链接
        image_patterns = [
            # 标准图片URL
            r"https?://[^\s]+\.(jpg|jpeg|png|gif|bmp|webp|svg|ico)(\?[^\s]*)?$",
            r"https?://[^\s]+\.(jpg|jpeg|png|gif|bmp|webp|svg|ico)(\?[^\s]*)?\s*$",
            # 包含图片关键词的URL
            r"https?://[^\s]*(image|img|photo|pic|avatar)[^\s]*$",
            r"https?://[^\s]*(image|img|photo|pic|avatar)[^\s]*\s*$",
            # 常见的图片服务域名
            r"https?://(picsum\.photos|unsplash\.com|images\.unsplash\.com|via\.placeholder\.com|placehold\.it)[^\s]*$",
            r"https?://(picsum\.photos|unsplash\.com|images\.unsplash\.com|via\.placeholder\.com|placehold\.it)[^\s]*\s*$",
        ]

        # 检查是否为图片URL
        for pattern in image_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True

        # 检查本地文件路径
        if os.path.isfile(text):
            ext = os.path.splitext(text)[1].lower()
            if ext in image_extensions:
                return True

        return False

    def _load_image(self, url_or_path):
        """加载图片并返回QPixmap"""
        try:
            if url_or_path.startswith(("http://", "https://")):
                # 网络图片
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }

                # 使用session来处理重定向
                session = requests.Session()
                session.headers.update(headers)

                # 允许重定向，设置超时
                response = session.get(url_or_path, timeout=15, allow_redirects=True)
                response.raise_for_status()

                # 检查响应内容类型
                content_type = response.headers.get("Content-Type", "").lower()
                if not content_type.startswith("image/"):
                    print(f"⚠️ 响应内容类型不是图片: {content_type}")
                    return None

                pixmap = QtGui.QPixmap()
                if pixmap.loadFromData(response.content):
                    return pixmap
                else:
                    print(f"⚠️ 无法加载图片数据")
                    return None
            else:
                # 本地图片
                pixmap = QtGui.QPixmap(url_or_path)
                if not pixmap.isNull():
                    return pixmap
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
        except Exception as e:
            print(f"❌ 加载图片失败: {e}")
        return None

    def _display_content(self, content):
        """显示内容，如果是图片则显示图片，否则显示文本"""
        if self._is_image_url(content):
            # 尝试加载图片
            pixmap = self._load_image(content)
            if pixmap:
                # 调整图片大小以适应窗口
                max_width = 400
                max_height = 300
                scaled_pixmap = pixmap.scaled(
                    max_width,
                    max_height,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation,
                )
                self.label.setPixmap(scaled_pixmap)
                self.label.setScaledContents(False)
                return

        # 如果不是图片或图片加载失败，显示文本
        self.label.clear()  # 清除所有内容（包括图片和文本）
        self.label.setText(content)

    def _apply_style_and_show(self, text: str):
        """
        专用于"PREVIEW::"模式：
        专用于"PREVIEW::"模式：
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

        # 2. 显示内容（图片或文本）
        self._display_content(text)

        # 3. 设置字体样式（无论是否为图片都设置，确保文本显示正确）
        font = QtGui.QFont(font_family, font_size)
        self.label.setFont(font)
        self.label.setStyleSheet(f"color: {font_color};")

        # 4. 调整窗口整体不透明度
        self.setWindowOpacity(window_opacity)

        # 5. 调整大小后再定位到屏幕右下或鼠标附近
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
        如果 raw_arg 以 "LOADING::" 开头，就进入"加载中…"模式并启动轮询。
        如果 raw_arg 以 "LOADING::" 开头，就进入"加载中…"模式并启动轮询。
        否则直接解码后显示完整文本。
        """
        decoded_arg = unquote_plus(raw_arg or "")
        if raw_arg and raw_arg.startswith("LOADING::"):
            parts = raw_arg.split("::", 1)
            if len(parts) == 2:
                uuid_str = parts[1]
                tmp_path = os.path.join(tempfile.gettempdir(), f"float_{uuid_str}.txt")
                self.label.setText("加载中…")
                # 应用样式设置
                self._apply_style()
                # 轮询定时器
                self._timer = QtCore.QTimer(self)
                self._timer.setInterval(300)
                self._timer.timeout.connect(lambda: self._check_temp_file(tmp_path))
                self._timer.start()
            else:
                # 格式异常，直接当普通显示
                self.label.setText(decoded_arg)
                self._apply_style()
        else:
            # 普通模式，直接显示
            self.label.setText(decoded_arg)
            self._apply_style()

    def _apply_style(self):
        """应用样式设置到标签和窗口"""
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

        # 2. 设置标签样式
        font = QtGui.QFont(font_family, font_size)
        self.label.setFont(font)
        self.label.setStyleSheet(f"color: {font_color};")

        # 3. 调整窗口整体不透明度
        self.setWindowOpacity(window_opacity)

    def _check_temp_file(self, tmp_path):
        """
        "加载中…"时定时轮询 tmp_path，如果文件内容有了，就更新 label 并调整大小、定位。
        "加载中…"时定时轮询 tmp_path，如果文件内容有了，就更新 label 并调整大小、定位。
        """
        try:
            if os.path.exists(tmp_path):
                with open(tmp_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    # 检查内容中是否包含图片URL
                    lines = content.split("\n")
                    image_urls = []
                    text_content = []

                    for line in lines:
                        line = line.strip()
                        if line and self._is_image_url(line):
                            image_urls.append(line)
                        elif line:
                            text_content.append(line)

                    # 如果有图片URL，显示所有图片
                    if image_urls:
                        # 清空之前的图片
                        while self.image_layout.count():
                            item = self.image_layout.takeAt(0)
                            if item.widget():
                                item.widget().deleteLater()

                        # 加载并显示所有图片
                        loaded_images = []
                        for img_url in image_urls:
                            pixmap = self._load_image(img_url)
                            if pixmap:
                                # 根据实际成功加载的图片数量动态调整大小
                                # 先添加到列表中，然后根据最终数量调整大小
                                scaled_pixmap = pixmap.scaled(
                                    200,
                                    200,  # 临时使用中等尺寸
                                    QtCore.Qt.KeepAspectRatio,
                                    QtCore.Qt.SmoothTransformation,
                                )

                                # 创建图片标签
                                img_label = QtWidgets.QLabel()
                                img_label.setPixmap(scaled_pixmap)
                                img_label.setScaledContents(False)
                                img_label.setStyleSheet(
                                    "border: 1px solid #666666; border-radius: 5px;"
                                )

                                # 添加到布局
                                self.image_layout.addWidget(img_label)
                                loaded_images.append(img_label)

                        # 根据实际成功加载的图片数量重新调整大小
                        if loaded_images:
                            actual_count = len(loaded_images)
                            img_size = self._calculate_image_size(actual_count)

                            # 重新调整所有已加载图片的大小
                            for img_label in loaded_images:
                                pixmap = img_label.pixmap()
                                if pixmap and not pixmap.isNull():
                                    scaled_pixmap = pixmap.scaled(
                                        img_size,
                                        img_size,
                                        QtCore.Qt.KeepAspectRatio,
                                        QtCore.Qt.SmoothTransformation,
                                    )
                                    img_label.setPixmap(scaled_pixmap)

                        # 如果有图片加载成功，显示图片区域
                        if loaded_images:
                            self.image_widget.show()
                            # 显示文本标签，让文本和图片同时显示
                            self.label.show()

                            # 根据实际成功加载的图片数量调整布局
                            self._adjust_layout_for_images(len(loaded_images))

                            # 如果有文本内容，显示在文本标签中
                            if text_content:
                                text_summary = "\n".join(text_content)
                                self.label.setText(text_summary)
                            else:
                                self.label.clear()
                        else:
                            # 所有图片加载失败，显示文本
                            self.image_widget.hide()
                            self.label.show()
                            self.label.clear()
                            self.label.setText(content)
                    else:
                        # 没有图片URL，显示文本
                        self.image_widget.hide()
                        self.label.show()
                        self.label.clear()
                        self.label.setText(content)

                    # 应用样式设置
                    self._apply_style()
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

                    # 如果是图片，根据图片大小调整窗口
                    if self.image_widget.isVisible() and self.image_layout.count() > 0:
                        # 计算图片区域的总宽度
                        total_width = 0
                        max_height = 0
                        actual_image_count = 0  # 实际显示的图片数量

                        for i in range(self.image_layout.count()):
                            item = self.image_layout.itemAt(i)
                            if (
                                item.widget()
                                and item.widget().pixmap()
                                and not item.widget().pixmap().isNull()
                            ):
                                total_width += item.widget().width()
                                max_height = max(max_height, item.widget().height())
                                actual_image_count += 1

                        # 加上间距和边距
                        spacing = self.image_layout.spacing()
                        margins = self.image_layout.contentsMargins()
                        total_width += (
                            spacing * (actual_image_count - 1)
                            + margins.left()
                            + margins.right()
                        )
                        max_height += margins.top() + margins.bottom()

                        # 计算文本区域的高度
                        text_height = 0
                        if self.label.isVisible() and self.label.text():
                            self.label.adjustSize()
                            text_height = self.label.height()

                        # 根据实际成功加载的图片数量动态调整窗口大小
                        if actual_image_count == 1:
                            # 单张图片：固定宽度，居中显示
                            window_width = 500
                            window_height = max_height + text_height + 30
                        else:
                            # 多张图片：根据图片总宽度调整
                            window_width = max(total_width, 500) + 30
                            window_height = max_height + text_height + 30

                        self.resize(window_width, window_height)
                    else:
                        # 没有图片，只显示文本
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
                        if x + self.width() + 5 > geo.right():
                            x = geo.right() - self.width() - 5
                        if y + self.height() + 5 > geo.bottom():
                            y = geo.bottom() - self.height() - 5
                        if x < geo.left() + 5:
                            x = geo.left() + 5
                        if y < geo.top() + 5:
                            y = geo.top() + 5
                    self.move(x, y)

        except Exception as e:
            print(f"❌ 检查临时文件时出错: {e}")  # 添加错误日志

    def showEvent(self, event: QtGui.QShowEvent):
        super().showEvent(event)
        self.activateWindow()
        self.setFocus(QtCore.Qt.MouseFocusReason)
        if self.initial_pos is None:
            self.initial_pos = self.pos()

    def focusOutEvent(self, event: QtGui.QFocusEvent):
        # 加载设置
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    wait_content = cfg.get("wait_content", False)
                    # 如果启用了等待内容加载完成，且内容未加载完成，则不关闭窗口
                    if wait_content and self.label.text() == "加载中…":
                        event.ignore()
                        return
        except:
            pass  # 如有任何错误，用默认行为

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

    def _calculate_image_size(self, image_count: int) -> int:
        """根据图片数量动态计算图片大小"""
        if image_count == 1:
            return 300  # 单张图片使用较大尺寸
        elif image_count == 2:
            return 200  # 两张图片使用中等尺寸
        elif image_count == 3:
            return 150  # 三张图片使用较小尺寸
        else:
            return 120  # 四张及以上使用最小尺寸

    def _adjust_layout_for_images(self, image_count: int):
        """根据图片数量调整布局"""
        if image_count == 1:
            # 单张图片居中
            self.image_layout.setAlignment(QtCore.Qt.AlignCenter)
        else:
            # 多张图片水平排列
            self.image_layout.setAlignment(QtCore.Qt.AlignLeft)


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
