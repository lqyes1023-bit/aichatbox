import os
from flask import Flask, request
from telegram import Bot
from anthropic import Anthropic

app = Flask(__name__)

# ===== 环境变量 =====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# ⚠️ CHAT_ID 不再需要（webhook模式自动获取）
bot = Bot(token=TELEGRAM_TOKEN)
client = Anthropic(api_key=ANTHROPIC_API_KEY)


# ===== Claude回复函数 =====
def ask_claude(text):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": text
        }]
    )
    return response.content[0].text.strip()


# ===== Telegram webhook入口 =====
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print("📩 RAW:", data)

        message = data.get("message", {})
        text = message.get("text")
        chat_id = message.get("chat", {}).get("id")

        print("💬 TEXT:", text)
        print("🆔 CHAT_ID:", chat_id)

        if not text or not chat_id:
            return "no message", 200

        # 👉 调 Claude
        reply = ask_claude(text)

        print("🤖 REPLY:", reply)

        # 👉 回 Telegram
        bot.send_message(chat_id=chat_id, text=reply)

        return "OK", 200

    except Exception as e:
        print("❌ ERROR:", str(e))
        return str(e), 500


# ===== 测试页面 =====
@app.route('/')
def home():
    return "Claude Telegram Bot Running ❤️"


# ===== 启动 =====
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )
