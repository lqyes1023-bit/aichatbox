import os
import traceback
from anthropic import Anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

MODEL = "claude-3-5-sonnet-20241022"


# =====================
# 1. API健康检测（只Claude）
# =====================
def probe_claude():
    try:
        res = client.messages.create(
            model=MODEL,
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": "ping"
            }]
        )
        print("✅ Claude API OK")
        return True

    except Exception as e:
        print("🔥 CLAUDE PROBE ERROR:", repr(e))
        return False


# =====================
# 2. 正式调用（关键）
# =====================
def ask_claude(user_text):
    try:
        res = client.messages.create(
            model=MODEL,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": user_text
            }]
        )

        return res.content[0].text.strip()

    except Exception as e:
        # ❗ 不再隐藏错误（重点）
        print("🔥 CLAUDE RUNTIME ERROR:")
        print(traceback.format_exc())

        return f"Claude调用失败：{repr(e)}"
