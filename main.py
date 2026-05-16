import os
import json
import traceback
from flask import Flask, request
from telegram import Bot
import anthropic
from datetime import datetime

app = Flask(__name__)

# =====================
# ENV
# =====================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)

client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY
)

# =====================
# CHAT HISTORY
# =====================

def load_history():
    try:
        with open("chat_history.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(history):
    with open("chat_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# =====================
# LOAD JSON
# =====================
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

memory = load_json("memory.json")
life_log = load_json("life_log.json")

# =====================
# PROMPT
# =====================
def build_prompt(user_text):
    return f"""
你是AI情感健康伴侣 K。

用户长期记忆：
{json.dumps(memory, ensure_ascii=False)}

生活记录：
{json.dumps(life_log, ensure_ascii=False)}

用户说：
{user_text}

请自然回复。
"""

# =====================
# Claude
# =====================
def ask_claude(text):

    history = load_history()

    history.append({
        "role": "user",
        "content": text
    })

    history = history[-15:]

    try:

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=history
        )

        reply = response.content[0].text

        print("🔥 CLAUDE SUCCESS:", reply)

        history.append({
            "role": "assistant",
            "content": reply
        })

        save_history(history)

        return reply

    except Exception as e:

        print("🔥 CLAUDE ERROR:")
        print(traceback.format_exc())

        return f"Claude错误: {str(e)}"
# =====================
# LIFE LOG
# =====================
def update_life_log(text):

    now = datetime.now().strftime("%Y-%m-%d")

    if "吃" in text:
        life_log.setdefault("diet", []).append({
            "time": now,
            "content": text
        })

    if "运动" in text or "健身" in text:
        life_log.setdefault("exercise", []).append({
            "time": now,
            "content": text
        })

    if "维生素" in text or "补剂" in text:
        life_log.setdefault("supplements", []).append({
            "time": now,
            "content": text
        })

    save_json("life_log.json", life_log)

# =====================
# WEBHOOK
# =====================
@app.route("/webhook", methods=["POST"])
def webhook():

    try:

        data = request.get_json()

        print("📩 RAW DATA:", data)

        text = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]

        print("📩 USER:", text)

        update_life_log(text)

        reply = ask_claude(text)

        print("🤖 FINAL:", reply)

        bot.send_message(
            chat_id=chat_id,
            text=reply
        )

        return "ok", 200

    except Exception as e:

        print("🔥 WEBHOOK ERROR:")
        print(traceback.format_exc())

        return "ok", 200

# =====================
# HOME
# =====================
@app.route("/")
def home():
    return "AI Life System Running", 200

# =====================
# RUN
# =====================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port
    )
