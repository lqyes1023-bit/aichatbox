```python id="z40q5n"
import os
from flask import Flask
import anthropic

app = Flask(__name__)

# =====================
# API KEY
# =====================
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

# =====================
# 自动扫描模型池
# =====================
MODEL_CANDIDATES = [

    # 新版
    "claude-3-5-sonnet-latest",
    "claude-3-5-sonnet-20241022",

    # 旧版
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307",

    # 未来可能版本
    "claude-3-7-sonnet",
    "claude-sonnet-4",
    "claude-opus-4",

    # 简写
    "claude-sonnet-4-20250514",
    "claude-opus-4-20250514",
]

# =====================
# TEST
# =====================
def test_model(model):

    try:

        res = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[
                {
                    "role": "user",
                    "content": "hi"
                }
            ]
        )

        return True

    except:
        return False

# =====================
# HOME
# =====================
@app.route("/")
def home():

    html = """
    <html>
    <head>
        <title>Claude Scanner</title>

        <style>

            body{
                background:#0f1117
```
