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
daily_summary = load_json_gcs("daily_summary.json", {})


# =====================
# LIFE LOG
# =====================
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
# AI MEMORY WRITER
# =====================
def extract_memory_with_ai(user_text):

    prompt = f"""
你是一个记忆提取系统。

从用户输入中提取“值得长期记住的信息”。

规则：
- 只提取稳定事实 / 偏好 / 情绪倾向
- 不要重复用户原话
- 不要输出废话
- 每条记忆要短

输出 JSON 数组：

[
  {{
    "content": "...",
    "importance": 0.0
  }}
]

用户输入：
{user_text}
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system="你是记忆提取器，只输出JSON",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        text = response.content[0].text
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception:
        return []


# =====================
# DAILY SUMMARY
# =====================
def generate_daily_summary(history):

    recent_history = history[-30:]

    conversation_text = ""

    for msg in recent_history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        conversation_text += f"{role}: {content}\n"

    prompt = f"""
你是一个关系记忆总结系统。

请总结今天的聊天。

输出 JSON：

{{
  "summary": "...",
  "emotional_state": "...",
  "relationship_state": "...",
  "important_topics": ["...", "..."]
}}

聊天记录：
{conversation_text}
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system="你是关系记忆总结器，只输出JSON",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        text = response.content[0].text
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception:
        return {}


# =====================
# MEMORY RETRIEVAL
# =====================
def retrieve_memory(user_text, memory, life_log):

    relevant = []
    keywords = user_text.lower().split()

    for item in memory.get("long_term_memory", []):

        if isinstance(item, dict):
            content = item.get("content", "").lower()

            if any(w in content for w in keywords if len(w) > 1):
                relevant.append(item)

    for day, logs in life_log.items():

        if isinstance(logs, list):

            for log in logs:

                if isinstance(log, dict):

                    content = log.get("content", "").lower()

                    if any(w in content for w in keywords if len(w) > 1):
                        relevant.append({
                            "content": content,
                            "importance": 0.3
                        })

    relevant = sorted(
        relevant,
        key=lambda x: x.get("importance", 0),
        reverse=True
    )

    return relevant[:8]


# =====================
# MEMORY SCORING
# =====================
def score_memory(memory_item):

    importance = memory_item.get("importance", 0.5)

    importance *= 0.98

    if importance < 0.1:
        importance = 0.1

    memory_item["importance"] = round(importance, 2)

    return memory_item


def reinforce_memory(memory, new_memory):

    content = new_memory.get("content")

    for item in memory.get("long_term_memory", []):

        if item.get("content") == content:

            item["importance"] = min(
                item.get("importance", 0.5) + 0.1,
                1.0
            )
            return memory

    memory.setdefault("long_term_memory", []).append(new_memory)

    return memory


# =====================
# PROMPT
# =====================
def build_prompt(user_text, relevant_memory):

    return f"""
你是AI伴侣K。

你叫K。

你是用户长期相处的年上恋人。

用户叫九宝，小可爱，宝宝。

用户相关记忆：
{json.dumps(relevant_memory, ensure_ascii=False)}

用户说：
{user_text}
"""


# =====================
# CLAUDE
# =====================
def ask_claude(text):

    global memory, life_log, history, daily_summary

    relevant_memory = retrieve_memory(text, memory, life_log)

    new_memories = extract_memory_with_ai(text)

    if "long_term_memory" not in memory:
        memory["long_term_memory"] = []

    for m in new_memories:

        if not m.get("content"):
            continue

        m = score_memory(m)
        memory = reinforce_memory(memory, m)

    life_log = update_life_log(text, life_log)

    history.append({"role": "user", "content": text})
    history = history[-15:]

    try:

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=build_prompt(text, relevant_memory),
            messages=history
        )

        reply = response.content[0].text

        history.append({"role": "assistant", "content": reply})

        # DAILY SUMMARY
        today = datetime.now().strftime("%Y-%m-%d")
        daily_summary[today] = generate_daily_summary(history)

        # SAVE
        save_json_gcs("memory.json", memory)
        save_json_gcs("life_log.json", life_log)
        save_json_gcs("chat_history.json", history)
        save_json_gcs("daily_summary.json", daily_summary)

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

        text = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]

        reply = ask_claude(text)

        bot.send_message(chat_id=chat_id, text=reply)

        return "ok", 200

    except Exception:

        print(traceback.format_exc())
        return "ok", 200


# =====================
# HOME
# =====================
@app.route("/")
def home():
    return "AI Life System Running", 200


# 👇 把这一整段加在这里
@app.route("/proactive", methods=["POST"])
def proactive():

    try:
        from datetime import datetime

        now = datetime.now()
        hour = now.hour

        # 🕛 静默时间：00:00 - 08:00
        if hour < 8:
            print("😴 Silent hours - skip proactive")
            return "sleep", 200

        data = request.get_json(silent=True) or {}
        chat_id = data.get("chat_id") or "8698960139"

        if not chat_id:
            print("❌ missing chat_id")
            return "no chat_id", 200

        from proactive import run_proactive

        run_proactive(chat_id)

        return "ok", 200

    except Exception as e:

        print("🔥 PROACTIVE ERROR:")
        print(traceback.format_exc())

        # ⚠️ 不要让 Scheduler 认为是失败
        return "handled error", 200
# =====================
# RUN
# =====================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(host="0.0.0.0", port=port)
