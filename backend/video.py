import os
import glob
import yt_dlp
import time


class AudioExtractor:
    def extract_audio(self, url):
        """下载音频并转换为讯飞API要求的格式"""
        if getattr(self, "debug", False):
            # 模拟网络请求延迟
            time.sleep(2)
            print("🔧 Debug模式：使用模拟音频内容")
            return "模拟音频文件路径"

        try:
            save_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "downloads"
            )
            os.makedirs(save_dir, exist_ok=True)

            print(f"\n🎵 开始提取音频：{url}")
            print(f"📂 保存目录：{save_dir}")

            ydl_opts = {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "wav",
                        "preferredquality": "0",
                    }
                ],
                "postprocessor_args": [
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                ],
                "outtmpl": os.path.join(save_dir, "%(title)s.%(ext)s"),
                "verbose": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # 获取最新下载的wav文件
            wav_files = glob.glob(os.path.join(save_dir, "*.wav"))
            if not wav_files:
                print("❌ 没有找到下载的音频文件！")
                return None

            audio_path = max(wav_files, key=os.path.getmtime)
            print(f"✅ 音频提取成功！文件路径：{audio_path}")
            return audio_path

        except Exception as e:
            print(f"❌ 异常错误：{e}")
            return None

    def delete_file(self, file_path):
        """删除指定文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ 已删除文件: {file_path}")
            else:
                print(f"⚠️ 文件不存在，无法删除: {file_path}")
        except Exception as e:
            print(f"❌ 删除文件失败: {file_path}，错误信息: {e}")
