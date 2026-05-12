import os
from flask import Flask, request
from telegram import Bot
from anthropic import Anthropic

app = Flask(__name__)

# ===== 环境变量 =====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# ===== 初始化 =====
bot = Bot(token=TELEGRAM_TOKEN)
client = Anthropic(api_key=ANTHROPIC_API_KEY)


# ===== Claude =====
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


# ===== Telegram webhook =====
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    print("🔥 RAW:", data)

    try:
        message = data.get("message", {})
        text = message.get("text")
        chat_id = message.get("chat", {}).get("id")

        print("💬 TEXT:", text)
        print("🆔 CHAT_ID:", chat_id)

        # ===== Claude =====
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": text
                }]
            )
            reply = response.content[0].text.strip()
            print("🤖 CLAUDE OK")
        except Exception as e:
            print("❌ CLAUDE FAIL:", str(e))
            return f"claude error: {str(e)}", 500

        # ===== Telegram =====
        try:
            result = bot.send_message(chat_id=chat_id, text=reply)
            print("📨 TG OK:", result)
        except Exception as e:
            print("❌ TG FAIL:", str(e))
            return f"telegram error: {str(e)}", 500

        return "OK", 200

    except Exception as e:
        print("❌ GLOBAL FAIL:", str(e))
        return str(e), 500

# ===== health check =====
@app.route('/')
def home():
    return "Claude Telegram Bot Running ❤️"


# ===== 启动 =====
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )
