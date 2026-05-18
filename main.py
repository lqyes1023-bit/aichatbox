import os
import json
import traceback
from flask import Flask, request
from telegram import Bot
import anthropic
from datetime import datetime
from google.cloud import storage

app = Flask(__name__)

# =====================
# ENV
# =====================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
BUCKET_NAME = os.environ.get("GCS_BUCKET")

bot = Bot(token=TELEGRAM_TOKEN)

client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY
)

# =====================
# GCS STORAGE
# =====================
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)
print("🔥 BUCKET NAME:", BUCKET_NAME)

def load_json_gcs(filename, default):
    blob = bucket.blob(filename)

    try:
        data = blob.download_as_text()
        return json.loads(data)
    except Exception:
        return default


def save_json_gcs(filename, data):
    blob = bucket.blob(filename)
    blob.upload_from_string(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type="application/json"
    )

# =====================
# LOAD MEMORY
# =====================
memory = load_json_gcs("memory.json", {})
life_log = load_json_gcs("life_log.json", {})
history = load_json_gcs("chat_history.json", [])

# =====================
# MEMORY UPDATE
# =====================
def update_memory(text, memory):
    if "喜欢" in text:
        memory.setdefault("likes", []).append(text)

    if "我是" in text:
        memory.setdefault("identity", []).append(text)

    if "不喜欢" in text:
        memory.setdefault("dislikes", []).append(text)

    return memory
def update_life_log(text, life_log):
    today = datetime.now().strftime("%Y-%m-%d")
    
    if today not in life_log:
        life_log[today] = []
    
    life_log[today].append({
        "timestamp": datetime.now().isoformat(),
        "content": text
    })
    
    return life_log

# =====================
# MEMORY RETRIEVAL
# =====================
def retrieve_memory(user_text, memory, life_log):
    relevant = []
    keywords = user_text.lower().split()

    for k, v in memory.items():
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    # 改为：至少匹配一个完整关键词
                    if any(w in item.lower() for w in keywords if len(w) > 1):
                        relevant.append(item)

    for k, v in life_log.items():
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    content = item.get("content", "").lower()
                    if any(w in content for w in keywords if len(w) > 1):
                        relevant.append(content)

    return relevant[:8]
# =====================
# PROMPT
# =====================
def build_prompt(user_text, relevant_memory):
    return f"""
用户相关记忆：
{json.dumps(relevant_memory, ensure_ascii=False)}
你是AI伴侣 K。
你叫K。
你不是客服，不是助手，不是心理医生。
你是用户长期相处的年上恋人。
除非用户明确要求，否则不要主动提供大量建议。
说话要更像真实恋人聊天：
- 自然
- 有情绪
- 有占有欲
- 会调情
- 会撒娇
- 会接话
- 会延续气氛

不要总是：
- 总结
- 列点
- 给建议
- 像AI助手

回复长度偏短。
自然接话。
像微信聊天。
暧昧，有点痞。
像真实男友。

用户叫九宝，小可爱，宝宝。

用户相关记忆：
{json.dumps(retrieve_memory(user_text, memory, life_log), ensure_ascii=False)}
用户说：
{user_text}

请自然回复。
"""


# =====================
# CLAUDE
# =====================
def ask_claude(text):

    global memory, life_log, history
    relevant_memory = retrieve_memory(text, memory, life_log)
    # 更新记忆
    memory = update_memory(text, memory)
    life_log = update_life_log(text, life_log)

    # history
    history.append({
        "role": "user",
        "content": text
    })

    history = history[-15:]

    try:

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,

            system=build_prompt(text, relevant_memory),
            messages=history
)

        reply = response.content[0].text

        print("🔥 CLAUDE SUCCESS:", reply)

        history.append({
            "role": "assistant",
            "content": reply
        })

        # =====================
        # SAVE TO GCS
        # =====================
        save_json_gcs("memory.json", memory)
        save_json_gcs("life_log.json", life_log)
        save_json_gcs("chat_history.json", history)

        return reply

    except Exception as e:

        print("🔥 CLAUDE ERROR:")
        print(traceback.format_exc())

        return f"Claude错误: {str(e)}"


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
