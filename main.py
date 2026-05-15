import os
import json
import traceback
from flask import Flask, request
from telegram import Bot
from anthropic import Anthropic
from datetime import datetime

app = Flask(__name__)

# =====================
# ENV
# =====================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# =====================
# LOAD JSON
# =====================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

memory = load_json("memory.json")
life_log = load_json("life_log.json")

# =====================
# SYSTEM PROMPT
# =====================
def build_prompt(user_text):
    return f"""
你是AI伴侣 K。

用户信息：
{memory}

生活记录：
{life_log}

用户输入：
{user_text}

如果用户提到饮食/运动/补剂：
- 自动整理成结构化记录（不需要解释）
"""

# =====================
# Claude
# =====================
def ask_claude(text):
    try:
        res = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=400,
            messages=[{"role": "user", "content": build_prompt(text)}]
        )
        return res.content[0].text.strip()

    except Exception as e:
        print(traceback.format_exc())
        return "我刚刚卡了一下，但我还在。"

# =====================
# 解析生活记录
# =====================
def update_life_log(text):
    now = datetime.now().strftime("%Y-%m-%d")

    if "吃" in text or "饮食" in text:
        life_log["diet"].append({
            "time": now,
            "content": text
        })

    if "跑" in text or "运动" in text or "健身" in text:
        life_log["exercise"].append({
            "time": now,
            "content": text
        })

    if "维生素" in text or "补剂" in text:
        life_log["supplements"].append({
            "time": now,
            "content": text
        })

    save_json("life_log.json", life_log)

# =====================
# WEBHOOK
# =====================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    text = data["message"]["text"]
    chat_id = data["message"]["chat"]["id"]

    reply = ask_claude(text)

    print("🔥 FINAL REPLY:", reply)

    bot.send_message(chat_id=chat_id, text=reply)

    return "ok", 200
# =====================
# HEALTH CHECK
# =====================
@app.route("/")
def home():
    return "AI Life System Running", 200

# =====================
# RUN
# =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
