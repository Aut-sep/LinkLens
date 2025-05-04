import os
import sys
from volcenginesdkarkruntime import Ark

class BaseBot:
    """公共基础类"""
    def _initialize_client(self) -> Ark:
        """共享的客户端初始化方法"""
        ak = os.getenv("VOLC_ACCESSKEY")
        sk = os.getenv("VOLC_SECRETKEY")
        if not ak or not sk:
            raise ValueError("请先设置环境变量 VOLC_ACCESSKEY 和 VOLC_SECRETKEY")
        return Ark(ak=ak, sk=sk, region="cn-beijing")
