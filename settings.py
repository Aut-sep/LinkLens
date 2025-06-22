# settings.py

import os
import json
import sys


class Settings:
    """
    使用 JSON 文件存储配置。默认路径：~/.linklens/config.json
    """

    def __init__(self, filename="config.json"):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".linklens")
        os.makedirs(self.config_dir, exist_ok=True)
        self.filename = os.path.join(self.config_dir, filename)

        # 默认配置项
        self.data = {
            "hotkey": "Alt+Shift+Q",
            "ARK_API_KEY": "",
            "VOLC_ACCESSKEY": "",
            "VOLC_SECRETKEY": "",
            "XFYUN_APP_ID": "",
            "XFYUN_API_KEY": "",
            "model": "",  # 如果留空，则可在程序里自动判断或使用默认值
            "font_family": "Sans Serif",
            "font_size": 12,
            "font_color": "#FFFFFF",
            "window_opacity": 0.8,
            "autostart": False,  # 如果 True，则创建开机启动文件
        }
        self._load()

    def _load(self):
        """从 JSON 文件加载配置，合并到默认 data 中。"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                    if isinstance(obj, dict):
                        # 合并已有 key
                        self.data.update(obj)
        except Exception as e:
            print(f"⚠️ 加载配置失败：{e}", file=sys.stderr)

    def save(self):
        """将当前 data 写回 JSON 文件。"""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 写入配置失败：{e}", file=sys.stderr)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()
