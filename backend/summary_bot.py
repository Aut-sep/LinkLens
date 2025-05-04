import sys
import os
import re
from typing import Optional
from colorama import Fore

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import BaseBot

class SummaryBot(BaseBot):
    def __init__(self):
        super().__init__()  # 初始化基类
        self.client = self._initialize_client()  # 添加客户端初始化
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
                "5. 最后换行并用【总结】结尾"
            )
        }

    def clean_text(self, raw_text: str) -> str:
        """文本清洗"""
        return re.sub(r'<.*?>|广告联系.*|\d{3}-\d{8}', '', raw_text)

    def auto_summarize(self, text: str, title: str) -> Optional[str]:
        """文本总结入口"""
        cleaned_text = self.clean_text(text)
        try:
            messages = [
                {"role": "system", "content": self.summary_config["system_prompt"]},
                {"role": "user", "content": f"标题：{title}\n正文：{cleaned_text}"}
            ]
            
            response = self.client.chat.completions.create(
                model=self.summary_config["model"],  # 修正为使用总结配置的模型
                messages=messages,
                temperature=self.summary_config["temperature"],
                max_tokens=self.summary_config["max_tokens"]
            )
            
            if response.choices:
                return self._format_summary(response.choices[0].message.content)
            return "总结生成失败"
            
        except Exception as e:
            print(f"{Fore.RED}总结失败: {str(e)}")
            return None
    
    def _format_summary(self, raw_text: str) -> str:
        """统一处理输出格式"""
        clean_text = raw_text.replace("**", "").replace("#", "")
        return '\n'.join([line.strip() for line in clean_text.split('\n') if line.strip()])