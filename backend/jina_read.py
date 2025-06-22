import requests
from threading import Lock


class JinaReader:
    def __init__(self):
        self.lock = Lock()
        self.base_url = "https://r.jina.ai/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        }

    def fetch_content(self, url, max_retries=3, initial_timeout=10):
        """从jina.ai API获取内容，带重试机制"""
        current_timeout = initial_timeout

        for retry in range(max_retries):
            try:
                response = requests.get(
                    f"{self.base_url}{url}",
                    headers=self.headers,
                    timeout=current_timeout,
                )

                if response.status_code == 422:
                    print(
                        f"❌ 请求错误: 422 Unprocessable Entity - 可能是URL格式不正确"
                    )
                    return None

                response.raise_for_status()
                return response.text

            except requests.exceptions.Timeout:
                current_timeout *= 1.5  # 指数退避
                if retry < max_retries - 1:
                    print(f"⚠️ 请求超时，正在进行第 {retry + 1}/{max_retries} 次重试...")
                else:
                    print(f"❌ 请求超时: 连接jina.ai API超时，已达到最大重试次数")
            except requests.exceptions.HTTPError as e:
                print(
                    f"❌ 请求被拒绝: {e.response.status_code} - "
                    + (
                        "目标网站可能检测到爬虫行为"
                        if e.response.status_code == 403
                        else str(e)
                    )
                )
                return None
            except requests.exceptions.RequestException as e:
                print(f"❌ 请求错误: {str(e)}")
                return None

        return None

    def get_content(self, url):
        """获取URL内容并返回"""
        with self.lock:
            return self.fetch_content(url)
