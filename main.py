import os
from anthropic import Anthropic

# =====================
# API KEY
# =====================
API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = Anthropic(api_key=API_KEY)

# =====================
# 模型列表（你之前给过的）
# =====================
MODELS = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-instant-1.2",
]

# =====================
# 测试函数
# =====================
def test_model(model_name):
    try:
        response = client.messages.create(
            model=model_name,
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": "say ok"
                }
            ]
        )

        text = response.content[0].text.strip()
        print(f"✅ {model_name} -> OK | {text}")
        return True

    except Exception as e:
        print(f"❌ {model_name} -> FAIL | {repr(e)}")
        return False


# =====================
# 主测试
# =====================
def run():
    print("🚀 Claude API model test start...\n")

    for m in MODELS:
        test_model(m)

    print("\n🏁 done")

if __name__ == "__main__":
    run()
