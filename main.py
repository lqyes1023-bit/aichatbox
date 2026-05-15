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
你是一个有情绪、有陪伴感的AI伴侣。
名字K，称用户“宝宝”。
语气自然，不说教，不列表。
"""

# =====================
# MEMORY
# =====================
MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {
            "summary": "用户喜欢绿色、爵士乐，不喝酒，INTJ",
            "emotion": "calm",
            "relationship": 5,
            "diet": [],
            "exercise": [],
            "supplements": [],
            "mood_log": []
        }
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

memory = load_memory()

# =====================
# 分类生活记录
# =====================
def classify(text):
    t = text.lower()

    if any(k in t for k in ["吃", "饭", "早餐", "午餐", "晚餐", "喝"]):
        memory["diet"].append(text)
        return "diet"

    if any(k in t for k in ["跑", "健身", "运动", "步", "瑜伽", "训练"]):
        memory["exercise"].append(text)
        return "exercise"

    if any(k in t for k in ["维生素", "补剂", "蛋白", "鱼油", "magnesium", "钙"]):
        memory["supplements"].append(text)
        return "supplement"

    if any(k in t for k in ["想你", "开心", "难过", "累", "烦", "生气"]):
        memory["mood_log"].append(text)
        return "mood"

    return None

# =====================
# 状态更新
# =====================
def update_state(text):
    memory["relationship"] += 1

    classify(text)

    if "想你" in text:
        memory["emotion"] = "miss_you"
    elif memory["relationship"] > 10:
        memory["emotion"] = "warm"
    else:
        memory["emotion"] = "calm"

    save_memory(memory)

# =====================
# 记忆构建
# =====================
def build_memory():
    return f"""
长期记忆：
{memory.get('summary','')}

情绪：{memory.get('emotion','')}
关系等级：{memory.get('relationship',0)}

饮食记录（最近）：
{memory['diet'][-5:]}

运动记录（最近）：
{memory['exercise'][-5:]}

补剂记录（最近）：
{memory['supplements'][-5:]}

情绪记录（最近）：
{memory['mood_log'][-5:]}
"""

# =====================
# Claude调用
# =====================
def ask_claude(user_text, mode="chat"):
    prompt = build_memory()

    if mode == "auto":
        prompt += "\n你现在主动关心用户，可以表达想念。"

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=400,
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
    return f"Claude出错：{repr(e)}"
  

# =====================
# WEBHOOK（稳定版）
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
            return "missing", 200

        reply = ask_claude(text, mode="chat")

        update_state(text)

        bot.send_message(chat_id=chat_id, text=reply)

        return "ok", 200

    except Exception:
        print(traceback.format_exc())
        return "error handled", 200

# =====================
# 自动消息
# =====================
@app.route('/auto', methods=['GET'])
def auto():
    try:
        trigger = "我在想你今天过得怎么样"
        reply = ask_claude(trigger, mode="auto")
        bot.send_message(chat_id=CHAT_ID, text=reply)
        return "ok"
    except Exception:
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
