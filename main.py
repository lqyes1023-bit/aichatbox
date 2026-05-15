
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
你是AI伴侣 K。

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

    prompt = build_prompt(text)

    try:

        response = client.messages.create(
            model="haiku",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        reply = response.content[0].text

        print("🔥 CLAUDE SUCCESS:", reply)

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
        print("✅ 1. 收到请求")
        
        text = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]
        print(f"✅ 2. 提取消息: {text}")
        
        update_life_log(text)
        print("✅ 3. 更新日志")
        
        reply = ask_claude(text)
        print(f"✅ 4. Claude 回复: {reply}")
        
        bot.send_message(
    chat_id=chat_id,
    text=reply
)
    print("✅ 消息已发送")
    
    return "ok", 200
except Exception as e:
    print(f"❌ 错误: {str(e)}")
    print(traceback.format_exc())
    return "ok", 200
# =====================
# RUN
# =====================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port
    )
