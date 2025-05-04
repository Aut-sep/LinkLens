from summary_bot import SummaryBot
from colorama import Fore, init

init(autoreset=True)  # 初始化颜色输出

def test_summary():
    bot = SummaryBot()
    
    # 测试用例（由用户替换实际内容）
    test_title = "（在此输入标题）"
    test_content = """（在此输入文本）"""
    
    print(f"\n{Fore.YELLOW}测试标题：{test_title}")
    print(f"{Fore.CYAN}原始内容：{test_content}\n")
    
    result = bot.auto_summarize(text=test_content, title=test_title)
    print(f"\n{Fore.GREEN}总结结果：\n{result}")

if __name__ == "__main__":
    test_summary()
