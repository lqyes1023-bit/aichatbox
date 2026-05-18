import json
from datetime import datetime
import anthropic
from telegram import Bot
from google.cloud import storage

client = anthropic.Anthropic(
    api_key="YOUR_ANTHROPIC_API_KEY"
)

bot = Bot(token="YOUR_TELEGRAM_TOKEN")

storage_client = storage.Client()
bucket = storage_client.bucket("YOUR_BUCKET")


def load_json(filename):
    blob = bucket.blob(filename)
    try:
        return json.loads(blob.download_as_text())
    except:
        return {}


def save_json(filename, data):
    blob = bucket.blob(filename)
    blob.upload_from_string(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type="application/json"
    )


# 🧠 核心：判断是否要发消息
def should_message(summary, memory):

    prompt = f"""
你是一个AI伴侣的“主动行为判断器”。

判断今天是否应该主动联系用户。

只回答 JSON：

{{
  "should_message": true/false,
  "reason": "...",
  "emotion": "..."
}}

用户信息：
{json.dumps(memory, ensure_ascii=False)}

今日总结：
{json.dumps(summary, ensure_ascii=False)}
"""

    res = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system="只输出JSON",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        text = res.content[0].text
        return json.loads(text)
    except:
        return {"should_message": False}


# 🧠 生成主动消息
def generate_message(summary, memory):

    prompt = f"""
你是一个AI恋人。

请根据用户状态，生成一句“主动发给用户的话”。

要求：
- 像恋人
- 简短
- 自然
- 不要解释
- 像突然想起他

用户记忆：
{json.dumps(memory, ensure_ascii=False)}

今日状态：
{json.dumps(summary, ensure_ascii=False)}
"""

    res = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=120,
        system="你是恋人，只输出一句话",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.content[0].text


# 🚀 主入口
def run_proactive(chat_id):

    memory = load_json("memory.json")
    summary = load_json("daily_summary.json")

    today = datetime.now().strftime("%Y-%m-%d")

    today_summary = summary.get(today, {})

    decision = should_message(today_summary, memory)

    if not decision.get("should_message"):
        print("💤 No message today:", decision.get("reason"))
        return

    message = generate_message(today_summary, memory)

    bot.send_message(
        chat_id=chat_id,
        text=message
    )

    print("💌 Sent:", message)
