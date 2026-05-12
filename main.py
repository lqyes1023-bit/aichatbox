import os
import random
from datetime import datetime
from flask import Flask
from telegram import Bot
from anthropic import Anthropic

app = Flask(__name__)

# ===== 环境变量 =====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# ===== 基础检查（防止静默失败）=====
if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_TOKEN 未设置")

if not CHAT_ID:
    print("❌ CHAT_ID 未设置")

if not ANTHROPIC_API_KEY:
    print("❌ ANTHROPIC_API_KEY 未设置")

# ===== 客户端 =====
bot = Bot(token=TELEGRAM_TOKEN)
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ===== Prompt =====
prompts = [
    "用温柔甜蜜但自然的语气，生成一条今天想念对方的短消息（50字以内），可以带一点今天的心情或小想法。",
    "像贴心伴侣一样，说一句想你、关心对方日常的话，文艺细腻一点。",
    "生成一条暖心小情绪，用第一人称表达今天突然想到对方。",
    "写一条'有点想你啦'的感觉，温暖、真诚，不要太夸张。"
]

# ===== Claude + Telegram =====
@app.route('/send', methods=['GET', 'POST'])
def send_message():
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            temperature=0.8,
            messages=[{
                "role": "user",
                "content": random.choice(prompts) + f" 当前时间: {datetime.now().strftime('%H:%M')}"
            }]
        )

        message = response.content[0].text.strip()

        # 👉 Telegram发送 + 打印返回值（关键调试）
        result = bot.send_message(
            chat_id=CHAT_ID,
            text=message
        )

        print("📨 Telegram response:", result)

        return f"✅ 已发送: {message}", 200

    except Exception as e:
        print("❌ ERROR:", str(e))
        return f"错误: {str(e)}", 500


# ===== Telegram测试 =====
@app.route('/test')
def test_telegram():
    try:
        result = bot.send_message(
            chat_id=CHAT_ID,
            text="👋 Telegram测试成功"
        )
        print("📨 TEST response:", result)
        return "OK", 200
    except Exception as e:
        print("❌ TEST ERROR:", str(e))
        return str(e), 500


# ===== 健康检查 =====
@app.route('/')
def home():
    return "AI Bot 运行中 ❤️ /send /test 可用"


# ===== 启动 =====
if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8080))
    )
