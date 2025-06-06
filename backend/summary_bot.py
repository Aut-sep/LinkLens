# backend/summary_bot.py

import sys
import os
import re
import time
import requests
from typing import Optional
from colorama import Fore
from bs4 import BeautifulSoup

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.common import BaseBot


class SummaryBot(BaseBot):
    def __init__(self):
        super().__init__()  # 初始化基类
        self.client = self._initialize_client()  # 添加客户端初始化
        self.timeout = 10  # 默认超时时间(秒)
        self.max_retries = 3  # 最大重试次数
        self.summary_config = {
            "model": "doubao-1.5-lite-32k-250115",
            "temperature": 0.3,
            "max_tokens": 500,
            "system_prompt": (
                "你是一个专业的内容总结助手。请严格遵循以下要求：\n"
                "1. 专注于分析用户提供的网页正文内容\n"
                "2. 根据文章标题确定核心主题\n"
                "3. 忽略与文章主体无关的广告、推广信息\n"
                "4. 使用简洁的bullet points格式输出（3-5个要点）\n"
                "5. 最后【总结】全文"
            ),
        }

    def clean_text(self, raw_text: str) -> str:
        """文本清洗"""
        return re.sub(r"<.*?>|广告联系.*|\d{3}-\d{8}", "", raw_text)

    def auto_summarize(self, text: str, title: str) -> Optional[str]:
        """文本总结入口"""
        if getattr(self, "debug", False):
            # 模拟网络请求延迟
            time.sleep(2)
            return (
                "📝 模拟网页内容总结：\n\n"
                "- 这是第一条重要信息，描述了文章的主要观点\n"
                "- 第二条信息补充了更多细节，帮助理解核心内容\n"
                "- 第三条信息提供了具体的例子和说明\n"
                "- 第四条信息总结了文章的主要结论\n\n"
                "【总结】这是一篇关于人工智能发展的文章，讨论了当前的技术进展和未来趋势。"
            )

        cleaned_text = self.clean_text(text)
        try:
            messages = [
                {"role": "system", "content": self.summary_config["system_prompt"]},
                {"role": "user", "content": f"标题：{title}\n正文：{cleaned_text}"},
            ]

            for attempt in range(self.max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=self.summary_config["model"],
                        messages=messages,
                        temperature=self.summary_config["temperature"],
                        max_tokens=self.summary_config["max_tokens"],
                        timeout=self.timeout,
                    )
                    break
                except requests.exceptions.Timeout:
                    if attempt == self.max_retries - 1:
                        raise
                    time.sleep(1)  # 等待1秒后重试

            if response.choices:
                return self._format_summary(response.choices[0].message.content)
            return "总结生成失败"

        except Exception as e:
            print(f"{Fore.RED}总结失败: {str(e)}")
            return None

    def _format_summary(self, raw_text: str) -> str:
        """统一处理输出格式"""
        clean_text = raw_text.replace("**", "").replace("#", "")
        return "\n".join(
            [line.strip() for line in clean_text.split("\n") if line.strip()]
        )

    def get_summary(self, url: str) -> Optional[str]:
        """
        公共方法：获取URL内容的摘要
        Args:
            url: 要摘要的URL
        Returns:
            格式化后的摘要内容或None
        """
        if getattr(self, "debug", False):
            # 模拟网络请求延迟，方便前端显示"加载中…"效果
            time.sleep(2)
            return (
                "模拟测试摘要：\n"
                "- 核心内容要点总结1\n"
                "- 核心内容要点总结2\n"
                "- 核心内容要点总结3\n"
                "- 核心内容要点总结4\n"
                "- 核心内容要点总结5\n"
                "【总结】测试用模拟摘要，这段文字共计约70 tokens"
            )

        try:
            # 获取网页内容
            response = requests.get(url)
            response.raise_for_status()

            # 提取标题和正文
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string if soup.title else "无标题"
            text = soup.get_text()

            # 调用自动摘要
            return self.auto_summarize(text, title)

        except Exception as e:
            print(f"{Fore.RED}获取摘要失败: {str(e)}")
            return None
