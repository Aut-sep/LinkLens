import os
import sys
import platform
from typing import List, Dict
from volcenginesdkarkruntime import Ark
from colorama import Fore, Style, init

# Windows 专用输入处理
if platform.system() == "Windows":
    try:
        import pyreadline3 as readline
    except ImportError:
        print("请先安装 pyreadline3: pip install pyreadline3")
        sys.exit(1)
else:
    import readline

# 初始化颜色输出
init(autoreset=True)

class VolcEngineChatBot:
    def __init__(self):
        self.client = self._initialize_client()
        self.conversation_history: List[Dict[str, str]] = []
        self.history_file = os.path.expanduser("~/.volc_chat_history")
        self._setup_readline()
        
        # 模型参数配置
        self.config = {
            "model": "doubao-1.5-lite-32k-250115",
            "temperature": 0.7,
            "max_tokens": 2000,
            "max_history": 8  # 保留最近4轮对话
        }

    def _initialize_client(self) -> Ark:
        """初始化火山引擎客户端"""
        try:
            ak = os.getenv("VOLC_ACCESSKEY")
            sk = os.getenv("VOLC_SECRETKEY")
            
            if not ak or not sk:
                raise ValueError(
                    f"{Fore.RED}错误：请先设置环境变量 VOLC_ACCESSKEY 和 VOLC_SECRETKEY"
                )
                
            return Ark(
                ak=ak,
                sk=sk,
                region="cn-beijing"
            )
        except Exception as e:
            print(f"{Fore.RED}初始化失败: {str(e)}")
            sys.exit(1)

    def _setup_readline(self):
        """配置输入历史记录"""
        if platform.system() != "Windows":
            try:
                readline.read_history_file(self.history_file)
            except FileNotFoundError:
                pass
                
        # 设置自动补全
        if platform.system() == "Windows":
            self.rl = readline.Readline()
            self.rl.set_completer(self._command_completer)
            self.rl.parse_and_bind("tab: complete")  # 使用Readline实例的方法
        else:
            readline.set_completer(self._command_completer)
            readline.parse_and_bind("tab: complete")
        
        # 设置历史记录长度
        if platform.system() != "Windows":
            readline.set_history_length(100)

    def _command_completer(self, text: str, state: int):
        """自定义命令自动补全"""
        commands = ['quit', 'help', 'clean', 'save']
        options = [cmd for cmd in commands if cmd.startswith(text)]
        return options[state] if state < len(options) else None

    def _handle_special_commands(self, input_str: str) -> bool:
        """处理特殊命令"""
        cmd = input_str.lower()
        
        if cmd in ['quit', 'exit', '退出']:
            print(f"\n{Fore.RED}Linklens 已关闭")
            sys.exit(0)
            
        if cmd == 'help':
            print(f"\n{Fore.CYAN}可用命令：")
            print(f"{Fore.GREEN}quit      - 结束对话")
            print(f"{Fore.GREEN}clean  - 重置对话上下文")
            print(f"{Fore.GREEN}save  - 手动保存输入记录")
            return True
            
        if cmd == 'clean':
            self.conversation_history.clear()
            print(f"{Fore.YELLOW}已清空对话历史")
            return True
            
        if cmd == 'save':
            readline.write_history_file(self.history_file)
            print(f"{Fore.YELLOW}已保存输入历史")
            return True
            
        return False

    def _print_response(self, text: str):
        """带格式打印响应"""
        lines = text.split('\n')
        print(f"\n{Fore.BLUE}Linklens：{Style.RESET_ALL}")
        for line in lines:
            print(f"{Fore.CYAN}│ {line}")

    def _truncate_history(self):
        """控制对话历史长度"""
        if len(self.conversation_history) > self.config["max_history"] * 2:
            self.conversation_history = self.conversation_history[-self.config["max_history"] * 2:]

    def start_chat(self):
        """启动对话循环"""
        print(f"{Fore.GREEN}\n Linklens 已启动...（输入 help 查看命令）")
        
        while True:
            try:
                # 彩色输入提示
                user_input = input(f"{Fore.YELLOW}\n您：{Style.RESET_ALL}")
                
                if self._handle_special_commands(user_input.strip()):
                    continue
                    
                # 添加到对话历史
                self.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # API 调用
                response = self.client.chat.completions.create(
                    model=self.config["model"],
                    messages=self.conversation_history,
                    temperature=self.config["temperature"],
                    max_tokens=self.config["max_tokens"]
                )
                
                # 处理响应
                if response.choices:  # 直接访问 choices 属性
                    bot_response = response.choices[0].message.content
                    self._print_response(bot_response)
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": bot_response
                    })
                    self._truncate_history()
                else:
                    print(f"{Fore.RED}错误：收到空响应")

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}检测到中断，输入 quit 结束对话")
            except Exception as e:
                print(f"{Fore.RED}API 错误：{str(e)}")
                self.conversation_history.clear()

if __name__ == "__main__":
    bot = VolcEngineChatBot()
    bot.start_chat()