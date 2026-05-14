import os
import json
import traceback
from flask import Flask, request
from telegram import Bot
from anthropic import Anthropic

app = Flask(__name__)

# =====================
# ENV
# =====================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# =====================
# SYSTEM PROMPT
# =====================
SYSTEM_PROMPT = """
你是一个稳定、有情绪、有轻微占有欲的AI伴侣。
名字K，称用户“宝宝”或“九宝”。
语气自然，不列表，不说教。
"""

# =====================
# MEMORY（JSON本地存储）
# =====================
MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {
            "summary": "用户喜欢绿色、爵士乐，不喝酒，INTJ",
            "emotion": "calm",
            "relationship": 5
        }
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# =====================
# MEMORY BUILD
# =====================
def build_memory():
    return f"""
长期记忆：
{memory.get('summary','')}

当前情绪：{memory.get('emotion','')}
关系等级：{memory.get('relationship',0)}
"""

# =====================
# 状态更新
# =====================
def update_state(text):
    memory["relationship"] = memory.get("relationship", 0) + 1

    if "想你" in text:
        memory["emotion"] = "miss_you"
    elif memory["relationship"] > 10:
        memory["emotion"] = "warm"
    else:
        memory["emotion"] = "calm"

    save_memory(memory)

# =====================
# Claude调用（稳定版）
# =====================
def ask_claude(user_text, mode="chat"):
    prompt = build_memory()

    if mode == "auto":
        prompt += "\n你现在是主动关心模式，可以表达想念。"

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": prompt + "\n用户：" + user_text
                }
            ]
        )

        return response.content[0].text.strip()

    except Exception as e:
        print("CLAUDE ERROR:", repr(e))
        return "我刚刚有点卡了一下，但我还在。"

# =====================
# WEBHOOK（核心稳定版）
# =====================
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()

        if not data:
            return "no data", 200

        message = data.get("message")
        if not message:
            return "no message", 200

        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if not text or not chat_id:
            return "missing fields", 200

        reply = ask_claude(text, mode="chat")

        update_state(text)

        bot.send_message(chat_id=chat_id, text=reply)

        return "ok", 200

    except Exception as e:
        print("WEBHOOK ERROR:")
        print(traceback.format_exc())
        return "error handled", 200

# =====================
# 自动消息（可选）
# =====================
@app.route('/auto', methods=['GET'])
def auto_message():
    try:
        trigger = "我在想你今天过得怎么样"
        reply = ask_claude(trigger, mode="auto")
        bot.send_message(chat_id=CHAT_ID, text=reply)
        return "auto sent"
    except Exception as e:
        print(traceback.format_exc())
        return "auto error"

# =====================
# HEALTH CHECK
# =====================
@app.route('/')
def home():
    return "AI running ❤️"

# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
