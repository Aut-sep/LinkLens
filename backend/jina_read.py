import requests
import time
from threading import Lock

class JinaReader:
    def __init__(self, api_key="jina_8c7819233de841f5b2bd71f0d413f00668hcCIe0bZVQ4c7JAFiz0tAQxTQ0"):
        self.lock = Lock()
        self.api_key = api_key
        self.base_url = "https://r.jina.ai/"
        
    def fetch_content(self, url, max_retries=3, initial_timeout=10):
        """ 从jina.ai API获取内容，带重试机制 """
        retry_count = 0
        current_timeout = initial_timeout
        
        while retry_count < max_retries:
            try:
                full_url = f"{self.base_url}{url}"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2"
                }
                
                response = requests.get(full_url, headers=headers, timeout=current_timeout)
                
                if response.status_code == 422:
                    print(f"❌ 请求错误: 422 Unprocessable Entity - 可能是URL格式不正确")
                    return None
                    
                response.raise_for_status()
                
                return response.text
                
            except requests.exceptions.Timeout:
                retry_count += 1
                current_timeout *= 1.5  # 指数退避
                print(f"⚠️ 请求超时，正在进行第 {retry_count}/{max_retries} 次重试...")
                if retry_count >= max_retries:
                    print(f"❌ 请求超时: 连接jina.ai API超时，已达到最大重试次数")
                    return None
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    print(f"❌ 请求被拒绝(403): 目标网站可能检测到爬虫行为，请尝试更换User-Agent或使用代理")
                else:
                    print(f"❌ 请求错误: {str(e)}")
                return None
            except requests.exceptions.RequestException as e:
                print(f"❌ 请求错误: {str(e)}")
                return None
        
        return None
            
    def get_content(self, url):
        """ 获取URL内容并返回(无打印输出) """
        with self.lock:
            return self.fetch_content(url)
            
    def run(self, url):
        """ 执行读取并打印结果 """
        print(f"🔍 正在从 {url} 获取内容...")
        content = self.get_content(url)
        
        if content:
            print(f"✅ 获取成功:\n{content}")
        else:
            print("⚠️ 未能获取内容")

if __name__ == "__main__":
    reader = JinaReader()
    reader.run("https://example.com")