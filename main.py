import os
import traceback
from anthropic import Anthropic

# =====================
# CLIENT
# =====================
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# =====================
# 🔥 只保留“历史上长期稳定模型”
# （避免所有 404 新模型坑）
# =====================
MODEL_POOL = [
    "claude-3-sonnet-20240229",   # 主力稳定
    "claude-3-haiku-20240307",    # 备用轻量
]

ACTIVE_MODEL = None


# =====================
# 1. 安全测试模型
# =====================
def safe_test(model):
    try:
        client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "ping"}]
        )
        print(f"✅ Model OK: {model}")
        return True

    except Exception as e:
        print(f"❌ Model FAIL: {model} -> {repr(e)}")
        return False


# =====================
# 2. 自动选择最稳模型（只执行一次）
# =====================
def select_model():
    global ACTIVE_MODEL

    if ACTIVE_MODEL:
        return ACTIVE_MODEL

    print("🧠 Selecting best available Claude model...")

    for m in MODEL_POOL:
        if safe_test(m):
            ACTIVE_MODEL = m
            print(f"🎯 ACTIVE MODEL LOCKED: {m}")
            return m

    raise Exception("No usable Claude model for this API key")


# =====================
# 3. 对外唯一入口（不会踩坑）
# =====================
def ask_claude(text):
    try:
        model = select_model()

        res = client.messages.create(
            model=model,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        return res.content[0].text.strip()

    except Exception as e:
        print("🔥 RUNTIME ERROR:")
        print(traceback.format_exc())

        # 永远不炸 webhook
        return f"我刚刚有点卡住了，但我还在。({repr(e)})"
