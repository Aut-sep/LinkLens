# backend/common.py

import os
import sys
from volcenginesdkarkruntime import Ark


class BaseBot:
    """公共基础类"""

    def __init__(self, settings=None):
        self.settings = settings

    def _initialize_client(self) -> Ark:
        """共享的客户端初始化方法"""
        if self.settings:
            ak = self.settings.get("VOLC_ACCESSKEY", "")
            sk = self.settings.get("VOLC_SECRETKEY", "")
        else:
            ak = ""
            sk = ""
        if not ak or not sk:
            # 不抛异常，返回None
            return None
        return Ark(ak=ak, sk=sk, region="cn-beijing")
