import base64
import hashlib
import hmac
import json
import os
import time
import requests
from urllib.parse import quote_plus
import logging

# 讯飞语音转写API配置
APP_ID = os.getenv("XFYUN_APP_ID")
API_KEY = os.getenv("XFYUN_API_KEY")

if not APP_ID or not API_KEY:
    raise ValueError("请设置环境变量 XFYUN_APP_ID 和 XFYUN_API_KEY")

# API URL
UPLOAD_URL = "https://raasr.xfyun.cn/v2/api/upload"
RESULT_URL = "https://raasr.xfyun.cn/v2/api/getResult"


def md5(text):
    """计算MD5哈希值"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def generate_signa(app_id, ts, secret_key):
    """生成签名参数signa"""
    logging.info(f"[签名] 开始生成签名: app_id={app_id}, ts={ts}")
    base_string = app_id + str(ts)
    md5_digest = md5(base_string)
    hmac_digest = hmac.new(
        secret_key.encode("utf-8"), md5_digest.encode("utf-8"), digestmod=hashlib.sha1
    ).digest()
    signa = base64.b64encode(hmac_digest).decode()
    logging.info("[签名] 签名生成完成")
    return signa


def upload_audio(audio_file, file_size, duration):
    """上传音频文件"""
    logger = logging.getLogger(__name__)
    logger.info("\n===== Step 1: 上传音频文件 =====")

    ts = int(time.time())
    signa = generate_signa(APP_ID, ts, API_KEY)

    params = {
        "appId": APP_ID,
        "ts": ts,
        "signa": signa,
        "fileName": os.path.basename(audio_file),
        "fileSize": file_size,
        "duration": duration,
        "language": "cn",
        "audioMode": "fileStream",
        "standardWav": 0,
    }

    query_string = "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
    request_url = f"{UPLOAD_URL}?{query_string}"

    logger.info(f"[上传] 请求URL: {request_url}")
    logger.info(
        f"[上传] 读取音频文件: {audio_file}，大小: {file_size} bytes，时长估计: {duration} ms"
    )

    with open(audio_file, "rb") as f:
        audio_data = f.read()

    headers = {"Content-Type": "application/octet-stream"}

    try:
        logger.info("[上传] 发送请求中...")
        response = requests.post(request_url, data=audio_data, headers=headers)
        response.raise_for_status()

        result = response.json()
        logger.info("[上传] 响应结果:")
        logger.info(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get("code") == "000000":
            order_id = result.get("content", {}).get("orderId")
            if order_id:
                logger.info(f"[上传] 上传成功，订单ID: {order_id}")
                return order_id
            else:
                logger.error("[上传] 订单ID未获取到")
        else:
            logger.error(f"[上传] 上传失败: {result.get('descInfo')}")

        return None

    except requests.exceptions.HTTPError as e:
        logger.error(f"[上传] HTTP错误! 状态码: {e.response.status_code}")
        logger.error(f"[上传] 响应内容: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"[上传] 异常发生: {e}")
        return None


def get_task_result(order_id):
    """获取任务结果"""
    logger = logging.getLogger(__name__)
    logger.info("\n===== Step 2: 查询转写结果 =====")

    ts = int(time.time())
    signa = generate_signa(APP_ID, ts, API_KEY)

    params = {
        "appId": APP_ID,
        "ts": ts,
        "signa": signa,
        "orderId": order_id,
        "resultType": "transfer",
    }

    query_string = "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
    request_url = f"{RESULT_URL}?{query_string}"

    logger.info(f"[查询] 请求URL: {request_url}")

    try:
        logger.info("[查询] 发送请求中...")
        response = requests.post(request_url, files={})
        response.raise_for_status()

        result = response.json()
        logger.info("[查询] 响应结果:")
        logger.info(json.dumps(result, indent=2, ensure_ascii=False))

        return result

    except requests.exceptions.HTTPError as e:
        logger.error(f"[查询] HTTP错误! 状态码: {e.response.status_code}")
        logger.error(f"[查询] 响应内容: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"[查询] 异常发生: {e}")
        return None


class XunfeiSpeechRecognizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def transcribe(self, audio_file_path):
        self.logger.info(f"\n===== 识别流程开始，音频文件: {audio_file_path} =====")
        try:
            file_size = os.path.getsize(audio_file_path)
            # 粗略估算时长，实际可根据采样率和音频格式调整
            duration = int(file_size / (16000 * 2)) * 1000

            print(f"📊 音频信息：")
            print(f"   - 文件大小：{file_size / 1024 / 1024:.2f} MB")
            print(f"   - 估算时长：{duration / 1000:.1f} 秒")

            # Step 1: 上传音频
            print("\n📤 正在上传音频文件...")
            order_id = upload_audio(audio_file_path, file_size, duration)
            if not order_id:
                print("❌ 音频上传失败")
                return None
            print(f"✅ 音频上传成功，订单ID：{order_id}")

            # Step 2: 轮询获取转写结果
            print("\n⏳ 开始转写处理...")
            max_attempts = 10
            for attempt in range(max_attempts):
                print(f"🔄 第 {attempt + 1} 次尝试获取结果...")
                result = get_task_result(order_id)

                if not result:
                    print("❌ 获取结果失败，5秒后重试")
                    time.sleep(5)
                    continue

                order_info = result.get("content", {}).get("orderInfo", {})
                status = order_info.get("status")

                if status == 4:
                    print("✅ 转写完成，开始解析结果")
                    order_result = result.get("content", {}).get("orderResult")
                    if order_result:
                        try:
                            result_data = json.loads(order_result)
                            lattice = result_data.get("lattice", [])
                            if lattice:
                                text = ""
                                for item in lattice:
                                    json_1best = json.loads(
                                        item.get("json_1best", "{}")
                                    )
                                    rt = json_1best.get("st", {}).get("rt", [])
                                    for ws_item in rt:
                                        ws = ws_item.get("ws", [])
                                        for w_item in ws:
                                            cw = w_item.get("cw", [])
                                            for word in cw:
                                                text += word.get("w", "")
                                print("✅ 结果解析完成")
                                return text
                            else:
                                print("❌ 解析失败：结果为空")
                        except json.JSONDecodeError:
                            print("❌ 解析失败：JSON格式错误")
                    else:
                        print("❌ 识别结果为空")
                    break
                elif status in [0, 3]:
                    print(f"⏳ 处理中（状态：{status}），等待5秒...")
                    time.sleep(5)
                else:
                    print(f"❌ 处理失败（状态：{status}）")
                    fail_type = order_info.get("failType")
                    if fail_type:
                        print(f"❌ 失败类型：{fail_type}")
                    break
            else:
                print("❌ 超过最大尝试次数，未获得结果")

        except Exception as e:
            print(f"❌ 发生异常：{e}")

        print("🏁 识别流程结束")
        return None


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
    )

    recognizer = XunfeiSpeechRecognizer()
    result = recognizer.transcribe("test.wav")

    if result:
        print("\n最终识别结果:\n" + result)
    else:
        print("\n识别失败")
