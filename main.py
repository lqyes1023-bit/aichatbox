import os
from flask import Flask, request
from telegram import Bot
from anthropic import Anthropic

app = Flask(__name__)

# ===== 环境变量 =====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ===== Claude对话 =====
def ask_claude(user_text):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": user_text
        }]
    )
    return response.content[0].text.strip()


# ===== Telegram webhook入口 =====
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()

        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if not text:
            return "no text", 200

        reply = ask_claude(text)

        bot.send_message(chat_id=chat_id, text=reply)

        return "OK", 200

    except Exception as e:
        print("ERROR:", str(e))
        return str(e), 500


# ===== 测试用 =====
@app.route('/')
def home():
    return "Claude Telegram Bot Running ❤️"


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )
