# frontend/config_window.py

import os
import sys
import platform
import subprocess
from PyQt5 import QtWidgets, QtGui, QtCore

from settings import Settings
from frontend.float_window import show_floating  # 用于弹样例悬浮窗


class ConfigWindow(QtWidgets.QMainWindow):
    # 自定义信号：当热键改变且验证通过时发出，便于主流程重新注册
    hotkeyChanged = QtCore.pyqtSignal(str)
    # 添加调试模式变更信号
    debugChanged = QtCore.pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkLens 配置")
        self.resize(500, 550)

        # 添加标志，防止初始化时触发示例悬浮窗
        self._is_initializing = True

        # —— 0. 加载或创建 Settings 实例 —— #
        self.settings = Settings()

        # —— 1. 中央区域布局 —— #
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        v_layout = QtWidgets.QVBoxLayout(central)
        v_layout.setContentsMargins(15, 15, 15, 15)
        v_layout.setSpacing(12)

        # —— 2. "关闭时隐藏到托盘" 复选框 —— #
        # —— 2. "关闭时隐藏到托盘" 复选框 —— #
        self.hide_on_close_checkbox = QtWidgets.QCheckBox("关闭时隐藏到托盘")
        hide_flag = self.settings.get("hide_on_close", True)
        self.hide_on_close_checkbox.setChecked(hide_flag)
        v_layout.addWidget(self.hide_on_close_checkbox)
        self.hide_on_close_checkbox.stateChanged.connect(self.on_hide_on_close_changed)

        # —— 3. "热键设置" —— #
        # —— 3. "热键设置" —— #
        hotkey_label = QtWidgets.QLabel("快捷键")
        v_layout.addWidget(hotkey_label)

        self.hotkey_edit = QtWidgets.QKeySequenceEdit()
        saved_hotkey = self.settings.get("hotkey", "Alt+Shift+Q")
        # QKeySequence 能直接解析 "Alt+Shift+Q"
        self.hotkey_edit.setKeySequence(QtGui.QKeySequence(saved_hotkey))
        v_layout.addWidget(self.hotkey_edit)

        # 提示标签：显示"有效"或"无效"
        # 提示标签：显示"有效"或"无效"
        self.hotkey_status_label = QtWidgets.QLabel()
        self.hotkey_status_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        self.hotkey_status_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        font2 = QtGui.QFont()
        font2.setItalic(True)
        self.hotkey_status_label.setFont(font2)
        v_layout.addWidget(self.hotkey_status_label)

        # 绑定信号
        self.hotkey_edit.keySequenceChanged.connect(self.validate_and_apply_hotkey)

        # 立即进行一次验证显示
        QtCore.QTimer.singleShot(0, self.validate_and_apply_hotkey)

        # —— 4. "功能设置" 区域 —— #
        feature_group = QtWidgets.QGroupBox("功能设置")
        feature_layout = QtWidgets.QVBoxLayout()

        # 添加等待内容加载完成选项
        self.wait_content_checkbox = QtWidgets.QCheckBox("等待内容加载完成")
        self.wait_content_checkbox.setChecked(self.settings.get("wait_content", False))
        self.wait_content_checkbox.stateChanged.connect(self._on_wait_content_changed)
        feature_layout.addWidget(self.wait_content_checkbox)

        # 添加debug模式选项
        self.debug_checkbox = QtWidgets.QCheckBox("启用调试模式（使用模拟数据）")
        self.debug_checkbox.setChecked(self.settings.get("debug", False))
        self.debug_checkbox.stateChanged.connect(self._on_feature_changed)
        feature_layout.addWidget(self.debug_checkbox)

        # 添加图片提取选项
        self.extract_image_checkbox = QtWidgets.QCheckBox("启用图片提取")
        self.extract_image_checkbox.setChecked(self.settings.get("extract_image", True))
        self.extract_image_checkbox.stateChanged.connect(self._on_extract_image_changed)
        feature_layout.addWidget(self.extract_image_checkbox)

        # 添加音频内容总结选项
        self.summarize_audio_checkbox = QtWidgets.QCheckBox("启用音频内容总结")
        self.summarize_audio_checkbox.setChecked(
            self.settings.get("summarize_audio", True)
        )
        self.summarize_audio_checkbox.stateChanged.connect(
            self._on_summarize_audio_changed
        )
        feature_layout.addWidget(self.summarize_audio_checkbox)

        feature_group.setLayout(feature_layout)
        v_layout.addWidget(feature_group)

        # —— 5. "API Key 输入" 区域 —— #
        api_group = QtWidgets.QGroupBox("API 相关")
        api_layout = QtWidgets.QFormLayout(api_group)
        api_layout.setLabelAlignment(QtCore.Qt.AlignRight)

        # ARK_API_KEY
        self.ark_key_edit = QtWidgets.QLineEdit()
        self.ark_key_edit.setText(self.settings.get("ARK_API_KEY", ""))
        api_layout.addRow("ARK_API_KEY:", self.ark_key_edit)

        # VOLC_ACCESSKEY
        self.volc_ak_edit = QtWidgets.QLineEdit()
        self.volc_ak_edit.setText(self.settings.get("VOLC_ACCESSKEY", ""))
        api_layout.addRow("VOLC_ACCESSKEY:", self.volc_ak_edit)

        # VOLC_SECRETKEY
        self.volc_sk_edit = QtWidgets.QLineEdit()
        self.volc_sk_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.volc_sk_edit.setText(self.settings.get("VOLC_SECRETKEY", ""))
        api_layout.addRow("VOLC_SECRETKEY:", self.volc_sk_edit)

        # XFYUN_APP_ID
        self.xfyun_app_id_edit = QtWidgets.QLineEdit()
        self.xfyun_app_id_edit.setText(self.settings.get("XFYUN_APP_ID", ""))
        api_layout.addRow("XFYUN_APP_ID:", self.xfyun_app_id_edit)

        # XFYUN_API_KEY
        self.xfyun_api_key_edit = QtWidgets.QLineEdit()
        self.xfyun_api_key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.xfyun_api_key_edit.setText(self.settings.get("XFYUN_API_KEY", ""))
        api_layout.addRow("XFYUN_API_KEY:", self.xfyun_api_key_edit)

        v_layout.addWidget(api_group)

        self.ark_key_edit.editingFinished.connect(self.on_api_keys_changed)
        self.volc_ak_edit.editingFinished.connect(self.on_api_keys_changed)
        self.volc_sk_edit.editingFinished.connect(self.on_api_keys_changed)
        self.xfyun_app_id_edit.editingFinished.connect(self.on_api_keys_changed)
        self.xfyun_api_key_edit.editingFinished.connect(self.on_api_keys_changed)

        # —— 6. "模型型号" —— #
        model_hbox = QtWidgets.QHBoxLayout()
        model_label = QtWidgets.QLabel("模型型号")
        self.model_edit = QtWidgets.QLineEdit()
        self.model_edit.setText(self.settings.get("model", ""))
        model_hbox.addWidget(model_label)
        model_hbox.addWidget(self.model_edit)

        self.auto_detect_btn = QtWidgets.QPushButton("自动检测")
        model_hbox.addWidget(self.auto_detect_btn)
        v_layout.addLayout(model_hbox)

        self.model_edit.editingFinished.connect(self.on_model_changed)
        self.auto_detect_btn.clicked.connect(self.on_auto_detect_model)

        # —— 7. "界面风格" 设置 —— #
        style_group = QtWidgets.QGroupBox("悬浮窗样式")
        style_layout = QtWidgets.QFormLayout(style_group)
        style_layout.setLabelAlignment(QtCore.Qt.AlignRight)

        # 7.1 字体族
        self.font_combo = QtWidgets.QFontComboBox()
        saved_font = self.settings.get("font_family", "Sans Serif")
        self.font_combo.setCurrentFont(QtGui.QFont(saved_font))
        style_layout.addRow("字体 (Font)：", self.font_combo)
        self.font_combo.currentFontChanged.connect(self.on_style_changed)

        # 7.2 字号
        self.font_size_spin = QtWidgets.QSpinBox()
        self.font_size_spin.setRange(6, 48)
        self.font_size_spin.setValue(self.settings.get("font_size", 12))
        style_layout.addRow("字号 (Size)：", self.font_size_spin)
        self.font_size_spin.valueChanged.connect(self.on_style_changed)

        # 7.3 字体颜色
        color_hbox = QtWidgets.QHBoxLayout()
        self.font_color_edit = QtWidgets.QLineEdit()
        self.font_color_edit.setReadOnly(True)
        saved_color = self.settings.get("font_color", "#FFFFFF")
        self.font_color_edit.setText(saved_color)
        color_hbox.addWidget(self.font_color_edit)
        self.pick_color_btn = QtWidgets.QPushButton("选择颜色")
        color_hbox.addWidget(self.pick_color_btn)
        style_layout.addRow("字体颜色 (Color)：", color_hbox)
        self.pick_color_btn.clicked.connect(self.on_pick_color)

        # 7.4 窗口不透明度
        opacity_hbox = QtWidgets.QHBoxLayout()
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)  # 最小 20%，最大 100%
        saved_opacity = int(self.settings.get("window_opacity", 0.8) * 100)
        self.opacity_slider.setValue(saved_opacity)
        opacity_hbox.addWidget(self.opacity_slider)
        self.opacity_label = QtWidgets.QLabel(f"{saved_opacity}%")
        opacity_hbox.addWidget(self.opacity_label)
        style_layout.addRow("窗口不透明度 (Opacity)：", opacity_hbox)
        self.opacity_slider.valueChanged.connect(self.on_opacity_value_changed)
        self.opacity_slider.sliderReleased.connect(self.on_opacity_slider_released)

        style_group.setLayout(style_layout)
        v_layout.addWidget(style_group)

        # —— 8. "开机自启" 选项 —— #
        self.autostart_checkbox = QtWidgets.QCheckBox("开机自启 (Windows)")
        self.autostart_checkbox.setChecked(self.settings.get("autostart", False))
        v_layout.addWidget(self.autostart_checkbox)
        self.autostart_checkbox.stateChanged.connect(self.on_autostart_changed)

        v_layout.addStretch()

        # —— 9. 系统托盘图标 —— #
        self._create_tray_icon()
        self._is_hidden_to_tray = False

        # 初始化完成，允许触发示例悬浮窗
        self._is_initializing = False

    # —— 功能设置相关 —— #
    def _on_feature_changed(self, state):
        """处理功能选项变更"""
        sender = self.sender()
        if sender == self.debug_checkbox:
            self.settings.set("debug", bool(state))
            # 发出调试模式变更信号
            self.debugChanged.emit(bool(state))
        elif sender == self.extract_image_checkbox:
            self.settings.set("extract_image", bool(state))
        elif sender == self.summarize_audio_checkbox:
            self.settings.set("summarize_audio", bool(state))
        self.settings.save()

    def _on_wait_content_changed(self, state):
        """处理等待内容加载完成选项变化"""
        self.settings.set("wait_content", bool(state))
        self.settings.save()

    def _on_extract_image_changed(self, state):
        """处理图片提取选项变化"""
        self.settings.set("extract_image", bool(state))
        self.settings.save()

    def _on_summarize_audio_changed(self, state):
        """处理音频内容总结选项变化"""
        self.settings.set("summarize_audio", bool(state))
        self.settings.save()

    # —— 热键相关 —— #

    def validate_and_apply_hotkey(self):
        """
        用户修改热键后执行：
        1) 验证是否能被 pynput 正确解析并注册（"是否有效"）
        用户修改热键后执行：
        1) 验证是否能被 pynput 正确解析并注册（"是否有效"）
        2) 如果有效则把它存到 setting，并发出 hotkeyChanged 信号
        """
        seq = self.hotkey_edit.keySequence()
        key_str = seq.toString(QtGui.QKeySequence.NativeText)
        # QKeySequenceEmpty 时让它显示"无效"
        # QKeySequenceEmpty 时让它显示"无效"
        if seq.isEmpty():
            self.hotkey_status_label.setText("当前热键：<未设置>")
            self.hotkey_status_label.setStyleSheet("color: red;")
            return

        # 转为 pynput 可识别的格式，例如："Alt+Shift+Q" → "<alt>+<shift>+q"
        pynput_str = self._convert_qtseq_to_pynput(key_str)
        if not pynput_str:
            self.hotkey_status_label.setText("无效格式")
            self.hotkey_status_label.setStyleSheet("color: red;")
            return

        # 尝试临时注册到 GlobalHotKeys，验证是否可用
        from pynput.keyboard import GlobalHotKeys

        try:
            temp_listener = GlobalHotKeys({pynput_str: lambda: None})
            # 注册后立即停止，若无异常说明格式正确
            temp_listener.start()
            temp_listener.stop()
            # 有效
            self.hotkey_status_label.setText(f"有效：{key_str}")
            self.hotkey_status_label.setStyleSheet("color: green;")
            # 把设置写入 JSON
            self.settings.set("hotkey", key_str)
            # 发射信号，通知外部（MainProcessor）重新注册
            self.hotkeyChanged.emit(pynput_str)
        except Exception as e:
            # 如果有异常（如格式不支持），就认为"无效"
            # 如果有异常（如格式不支持），就认为"无效"
            self.hotkey_status_label.setText(f"无效：{e}")
            self.hotkey_status_label.setStyleSheet("color: red;")

    def _convert_qtseq_to_pynput(self, qt_seq_str: str) -> str:
        """
        把 QtKeySequence (NativeText，如 "Alt+Shift+Q") 转换为 pynput 需要的 "<alt>+<shift>+q"。
        只处理常见修饰符+单键字母/数字/功能键，复杂组合可能无法解析。
        """
        parts = qt_seq_str.split("+")
        parts = qt_seq_str.split("+")
        mapping = {
            "Ctrl": "ctrl",
            "Control": "ctrl",
            "Alt": "alt",
            "Shift": "shift",
            "Cmd": "cmd",
            "Meta": "cmd",
            "Meta": "cmd",
        }
        out_parts = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # 修饰符
            if part in mapping:
                out_parts.append(f"<{mapping[part]}>")
            else:
                # 单字符（字母或数字）或 F1~F12 等
                key = part.lower()
                # 如果是功能键 F1~F35，pynput 支持 "f1" 之类
                out_parts.append(key)
        return "+".join(out_parts)
        return "+".join(out_parts)

    # —— API Key 相关 —— #

    def on_api_keys_changed(self):
        self.settings.set("ARK_API_KEY", self.ark_key_edit.text().strip())
        self.settings.set("VOLC_ACCESSKEY", self.volc_ak_edit.text().strip())
        self.settings.set("VOLC_SECRETKEY", self.volc_sk_edit.text().strip())
        self.settings.set("XFYUN_APP_ID", self.xfyun_app_id_edit.text().strip())
        self.settings.set("XFYUN_API_KEY", self.xfyun_api_key_edit.text().strip())

    # —— 模型相关 —— #

    def on_model_changed(self):
        self.settings.set("model", self.model_edit.text().strip())

    def on_auto_detect_model(self):
        default = os.getenv("DEFAULT_MODEL", "")
        if not default:
            default = "doubao-1.5-lite-32k-250115"
        self.model_edit.setText(default)
        self.settings.set("model", default)
        QtWidgets.QMessageBox.information(
            self, "提示", f"已自动检测并设置模型：{default}"
        )
        QtWidgets.QMessageBox.information(
            self, "提示", f"已自动检测并设置模型：{default}"
        )

    # —— 界面风格相关 —— #

    def on_style_changed(self, *_):
        """
        当字体、字号、颜色变化时调用（不包括不透明度滑块）
        """
        fam = self.font_combo.currentFont().family()
        size = self.font_size_spin.value()
        self.settings.set("font_family", fam)
        self.settings.set("font_size", size)
        color = self.font_color_edit.text().strip()
        self.settings.set("font_color", color)

        # 3) 保存不透明度
        opacity = self.opacity_slider.value() / 100.0
        self.settings.set("window_opacity", opacity)
        self.opacity_label.setText(f"{self.opacity_slider.value()}%")

        # 只在非初始化状态下弹出示例悬浮窗
        if not getattr(self, "_is_initializing", False):
            show_floating("PREVIEW::示例文字")

    def on_pick_color(self):
        """弹出 QColorDialog，选好颜色后保存并触发 on_style_changed"""
        initial = QtGui.QColor(self.font_color_edit.text())
        color = QtWidgets.QColorDialog.getColor(initial, self, "选择字体颜色")
        if color.isValid():
            hex_color = color.name()
            self.font_color_edit.setText(hex_color)
            # 触发样式更新
            self.on_style_changed()

    # —— 开机自启相关 —— #

    def on_autostart_changed(self, state):
        enable = state == QtCore.Qt.Checked
        enable = state == QtCore.Qt.Checked
        self.settings.set("autostart", enable)
        self._update_autostart(enable)

    def _update_autostart(self, enable: bool):
        if platform.system() != "Windows":
            return

        python_exe = sys.executable
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        main_py = os.path.join(project_root, "main.py")
        startup_dir = os.path.join(
            os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu\Programs\Startup"
        )
        startup_dir = os.path.join(
            os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu\Programs\Startup"
        )
        os.makedirs(startup_dir, exist_ok=True)
        autostart_path = os.path.join(startup_dir, "LinkLens_autostart.bat")

        if enable:
            content = f'@echo off\n"{python_exe}" "{main_py}"\n'
            try:
                with open(autostart_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self, "开机自启", f"创建启动脚本失败：{e}"
                )
                QtWidgets.QMessageBox.warning(
                    self, "开机自启", f"创建启动脚本失败：{e}"
                )
        else:
            try:
                if os.path.exists(autostart_path):
                    os.remove(autostart_path)
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self, "开机自启", f"删除启动脚本失败：{e}"
                )
                QtWidgets.QMessageBox.warning(
                    self, "开机自启", f"删除启动脚本失败：{e}"
                )

    # —— 隐藏/退出选项 —— #

    def on_hide_on_close_changed(self, state):
        """同步"关闭时隐藏到托盘"选项到配置"""
        hide_flag = state == QtCore.Qt.Checked
        """同步"关闭时隐藏到托盘"选项到配置"""
        hide_flag = state == QtCore.Qt.Checked
        self.settings.set("hide_on_close", hide_flag)

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        根据"关闭时隐藏到托盘"复选框决定：隐藏或退出。
        根据"关闭时隐藏到托盘"复选框决定：隐藏或退出。
        """
        if self.hide_on_close_checkbox.isChecked():
            event.ignore()
            self._hide_to_tray()
        else:
            event.accept()
            QtWidgets.QApplication.instance().quit()

    def _create_tray_icon(self):
        tray_icon = self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)
        self.tray_icon = QtWidgets.QSystemTrayIcon(tray_icon, parent=self)

        tray_menu = QtWidgets.QMenu()
        show_action = tray_menu.addAction("显示设置窗口")
        exit_action = tray_menu.addAction("退出程序")

        show_action.triggered.connect(self._show_from_tray)
        exit_action.triggered.connect(self._exit_app)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self._show_from_tray()

    def _show_from_tray(self):
        if self._is_hidden_to_tray:
            self.show()
            self.activateWindow()
            self._is_hidden_to_tray = False
            self.tray_icon.hide()

    def _exit_app(self):
        QtWidgets.QApplication.instance().quit()

    def _hide_to_tray(self):
        self.hide()
        self._is_hidden_to_tray = True
        self.tray_icon.show()
        self.tray_icon.showMessage(
            "LinkLens 已最小化到托盘",
            '双击图标或在托盘菜单中选择"显示设置窗口"可恢复',
            QtWidgets.QSystemTrayIcon.Information,
            2000,
        )

    def on_opacity_value_changed(self, value):
        # 只更新label和保存设置，不弹预览
        opacity = value / 100.0
        self.settings.set("window_opacity", opacity)
        self.opacity_label.setText(f"{value}%")

    def on_opacity_slider_released(self):
        # 松手时弹出预览悬浮窗
        show_floating("PREVIEW::示例文字")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    w = ConfigWindow()
    w.show()
    sys.exit(app.exec_())
