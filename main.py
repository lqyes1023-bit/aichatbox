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

# 防止 Cloud Run 启动直接炸
if not TELEGRAM_TOKEN or not ANTHROPIC_API_KEY:
    print("❌ ENV missing: TELEGRAM_TOKEN or ANTHROPIC_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# =====================
# SYSTEM
# =====================
SYSTEM_PROMPT = """
你是一个稳定、有情绪、有陪伴感的AI伴侣。
名字K，称用户“宝宝”。
语气自然，不列表，不说教。
"""

# =====================
# MEMORY
# =====================
MEMORY_FILE = "memory.json"

def default_memory():
    return {
        "summary": "用户喜欢绿色、爵士乐，不喝酒，INTJ",
        "emotion": "calm",
        "relationship": 5,
        "diet": [],
        "exercise": [],
        "supplements": [],
        "mood_log": []
    }

def load_memory():
    try:
        if not os.path.exists(MEMORY_FILE):
            return default_memory()

        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 防止字段缺失炸掉
        base = default_memory()
        base.update(data)
        return base

    except Exception as e:
        print("MEMORY LOAD ERROR:", repr(e))
        return default_memory()

def save_memory(mem):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("MEMORY SAVE ERROR:", repr(e))

memory = load_memory()

# =====================
# 分类记录
# =====================
def classify(text):
    t = text.lower()

    if any(k in t for k in ["吃", "饭", "早餐", "午餐", "晚餐", "喝"]):
        memory["diet"].append(text)
        return "diet"

    if any(k in t for k in ["跑", "健身", "运动", "瑜伽", "训练", "步"]):
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
    memory["relationship"] = memory.get("relationship", 0) + 1

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

饮食：
{memory['diet'][-5:]}

运动：
{memory['exercise'][-5:]}

补剂：
{memory['supplements'][-5:]}

情绪记录：
{memory['mood_log'][-5:]}
"""

# =====================
# Claude
# =====================
def ask_claude(text, mode="chat"):
    prompt = build_memory()

    if mode == "auto":
        prompt += "\n你现在可以主动关心用户。"

    try:
        res = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": prompt + "\n用户：" + text
                }
            ]
        )

        return res.content[0].text.strip()

    except Exception as e:
        print("CLAUDE ERROR:", repr(e))
        return "我刚刚有点卡住了，但我还在。"

# =====================
# WEBHOOK
# =====================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        if not data:
            return "no data", 200

        msg = data.get("message")
        if not msg:
            return "no message", 200

        text = msg.get("text", "")
        chat_id = msg.get("chat", {}).get("id")

        if not text or not chat_id:
            return "missing", 200

        reply = ask_claude(text)

        update_state(text)

        bot.send_message(chat_id=chat_id, text=reply)

        return "ok", 200

    except Exception:
        print(traceback.format_exc())
        return "error handled", 200

# =====================
# HEALTH CHECK
# =====================
@app.route("/")
def home():
    print("🔥 Flask started successfully")
    return "AI running ❤️"

# =====================
# RUN (Cloud Run safe)
# =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
