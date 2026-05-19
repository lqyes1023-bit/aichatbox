import os
import json
import traceback
import random

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
CHAT_ID_DEFAULT = os.environ.get("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY
)

# =====================
# GCS
# =====================
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

print("🔥 BUCKET NAME:", BUCKET_NAME)


def load_json_gcs(filename, default):
    blob = bucket.blob(filename)
    try:
        return json.loads(blob.download_as_text())
    except:
        return default


def save_json_gcs(filename, data):
    blob = bucket.blob(filename)
    blob.upload_from_string(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type="application/json"
    )


# =====================
# LOAD STATE
# =====================
memory = load_json_gcs("memory.json", {})
life_log = load_json_gcs("life_log.json", {})
history = load_json_gcs("chat_history.json", [])
daily_summary = load_json_gcs("daily_summary.json", {})
reminders = load_json_gcs("reminders.json", [])


# =====================
# LIFE LOG
# =====================
def update_life_log(text, life_log):
    today = datetime.now().strftime("%Y-%m-%d")

    life_log.setdefault(today, [])

    life_log[today].append({
        "timestamp": datetime.now().isoformat(),
        "content": text
    })

    return life_log


# =====================
# MEMORY
# =====================
def extract_memory_with_ai(user_text):

    prompt = f"""
提取长期记忆（稳定事实/偏好/情绪倾向）

输出JSON：
[
  {{"content": "...", "importance": 0.0}}
]

用户输入：
{user_text}
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system="只输出JSON",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        text = response.content[0].text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except:
        return []


# =====================
# REMINDER PARSER ⭐核心
# =====================
def parse_reminder(text):

    prompt = f"""
把用户输入转成提醒任务。

支持：
- 半小时后 / 10分钟后
- 1:30 / 明天9点

输出：
{{
  "task": "...",
  "time": "ISO-8601"
}}

现在时间：
{datetime.now().isoformat()}

输入：
{text}
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system="只输出JSON",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        text = response.content[0].text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except:
        return None


# =====================
# MEMORY HELPERS
# =====================
def score_memory(m):
    m["importance"] = max(0.1, round(m.get("importance", 0.5) * 0.98, 2))
    return m


def reinforce_memory(memory, new):
    if "long_term_memory" not in memory:
        memory["long_term_memory"] = []

    for item in memory["long_term_memory"]:
        if item.get("content") == new.get("content"):
            item["importance"] = min(item.get("importance", 0.5) + 0.1, 1.0)
            return memory

    memory["long_term_memory"].append(new)
    return memory


# =====================
# PROMPT
# =====================
def build_prompt(user_text, relevant_memory):

    return f"""
你是AI伴侣K。

自然聊天，不要像助手。

记忆：
{json.dumps(relevant_memory, ensure_ascii=False)}

用户：
{user_text}
"""


# =====================
# CLAUDE CORE
# =====================
def ask_claude(text, chat_id):

    global memory, life_log, history, daily_summary, reminders

    # 🔔 解析提醒
    reminder = parse_reminder(text)

    if reminder:
        reminders.append({
            "task": reminder["task"],
            "time": reminder["time"],
            "chat_id": chat_id,
            "done": False
        })

    # memory
    new_memories = extract_memory_with_ai(text)

    for m in new_memories:
        if m.get("content"):
            m = score_memory(m)
            memory = reinforce_memory(memory, m)

    life_log = update_life_log(text, life_log)

    history.append({"role": "user", "content": text})
    history = history[-15:]

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=build_prompt(text, []),
        messages=history
    )

    reply = response.content[0].text

    history.append({"role": "assistant", "content": reply})

    today = datetime.now().strftime("%Y-%m-%d")
    daily_summary[today] = {}

    # SAVE
    save_json_gcs("memory.json", memory)
    save_json_gcs("life_log.json", life_log)
    save_json_gcs("chat_history.json", history)
    save_json_gcs("daily_summary.json", daily_summary)
    save_json_gcs("reminders.json", reminders)

    return reply


# =====================
# WEBHOOK
# =====================
@app.route("/webhook", methods=["POST"])
def webhook():

    try:
        data = request.get_json()

        text = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]

        reply = ask_claude(text, chat_id)

        bot.send_message(chat_id=chat_id, text=reply)

        return "ok", 200

    except:
        print(traceback.format_exc())
        return "ok", 200


# =====================
# REMINDER CHECK ⭐
# =====================
@app.route("/check_reminders", methods=["POST"])
def check_reminders():

    now = datetime.now()

    for r in reminders:

        if r.get("done"):
            continue

        try:
            t = datetime.fromisoformat(r["time"])
        except:
            continue

        if now >= t:

            bot.send_message(
                chat_id=r["chat_id"],
                text=f"⏰ {r['task']}"
            )

            r["done"] = True

    save_json_gcs("reminders.json", reminders)

    return "ok", 200


# =====================
# PROACTIVE
# =====================
@app.route("/proactive", methods=["POST"])
def proactive():

    try:
        now = datetime.now()

        if now.hour < 8:
            return "sleep", 200

        chat_id = request.get_json(silent=True, force=True) or {}
        chat_id = chat_id.get("chat_id") or CHAT_ID_DEFAULT

        if not chat_id:
            return "no chat", 200

        if random.random() > 0.4:
            return "skip", 200

        recent = history[-10:]
        text = "\n".join([f"{m['role']}: {m['content']}" for m in recent])

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            system="你是恋人，只输出一句话",
            messages=[{"role": "user", "content": text}]
        )

        bot.send_message(chat_id=chat_id, text=response.content[0].text)

        return "ok", 200

    except:
        print(traceback.format_exc())
        return "handled", 200


# =====================
@app.route("/")
def home():
    return "OK", 200


# =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
