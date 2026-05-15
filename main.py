import os
import traceback
from anthropic import Anthropic

# =====================
# Claude Client
# =====================
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# =====================
# 模型候选池（从新到旧）
# =====================
MODEL_POOL = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]

# =====================
# 全局缓存（关键优化）
# =====================
ACTIVE_MODEL = None


# =====================
# 单模型测试
# =====================
def test_model(model_name):
    try:
        client.messages.create(
            model=model_name,
            max_tokens=10,
            messages=[{"role": "user", "content": "ping"}]
        )
        print(f"✅ Model OK: {model_name}")
        return True

    except Exception as e:
        print(f"❌ Model FAIL: {model_name} -> {repr(e)}")
        return False


# =====================
# 启动时自动探测
# =====================
def init_model():
    global ACTIVE_MODEL

    if ACTIVE_MODEL:
        return ACTIVE_MODEL

    print("🧠 Starting Claude model detection...")

    for model in MODEL_POOL:
        if test_model(model):
            ACTIVE_MODEL = model
            print(f"🎯 Selected ACTIVE MODEL: {model}")
            return model

    raise Exception("No valid Claude model found for this API key")


# =====================
# 对外调用（你只用这个）
# =====================
def ask_claude(text):
    try:
        model = init_model()

        res = client.messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": text}]
        )

        return res.content[0].text.strip()

    except Exception as e:
        print("🔥 Claude runtime error:")
        print(traceback.format_exc())

        # runtime fallback（不影响系统）
        return f"我刚刚有点卡住了，但我还在。({repr(e)})"
