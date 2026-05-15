import os
import json
import traceback
from flask import Flask, request
from telegram import Bot
from anthropic import Anthropic

app = Flask(__name__)

# =====================
# 全局变量（先不初始化，避免启动炸）
# =====================
bot = None
client = None

# =====================
# SYSTEM PROMPT
# =====================
SYSTEM_PROMPT = """
你是一个稳定、有情绪、有陪伴感的AI。
语气自然，不列表，不说教。
"""

# =====================
# 初始化（延迟加载，防止Cloud Run启动失败）
# =====================
def init_clients():
    global bot, client

    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

    if not TELEGRAM_TOKEN:
        raise Exception("Missing TELEGRAM_TOKEN")

    if not ANTHROPIC_API_KEY:
        raise Exception("Missing ANTHROPIC_API_KEY")

    if bot is None:
        bot = Bot(token=TELEGRAM_TOKEN)

    if client is None:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)

# =====================
# Claude调用
# =====================
def ask_claude(text):
    try:
        res = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        return res.content[0].text.strip()

    except Exception as e:
        print("🔥 CLAUDE ERROR:")
        print(traceback.format_exc())
        return f"我刚刚有点卡住了，但我还在。({repr(e)})"

# =====================
# WEBHOOK（核心入口）
# =====================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        init_clients()

        data = request.get_json()

        if not data:
            return "ok", 200

        msg = data.get("message", {})
        text = msg.get("text")
        chat_id = msg.get("chat", {}).get("id")

        if not text or not chat_id:
            return "ok", 200

        reply = ask_claude(text)

        bot.send_message(chat_id=chat_id, text=reply)

        return "ok", 200

    except Exception as e:
        print("🔥 WEBHOOK ERROR:")
        print(traceback.format_exc())
        return "ok", 200

# =====================
# HEALTH CHECK（Cloud Run必须）
# =====================
@app.route("/")
def home():
    print("🔥 Flask is alive")
    return "AI running ❤️", 200


# =====================
# RUN（本地/Cloud Run兼容）
# =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
