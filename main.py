```python
import os
from flask import Flask
import anthropic

app = Flask(__name__)

# =====================
# API
# =====================
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

# =====================
# 模型池
# =====================
MODEL_CANDIDATES = [

    "claude-3-5-sonnet-latest",
    "claude-3-5-sonnet-20241022",

    "claude-3-haiku-20240307",

    "claude-3-sonnet-20240229",

    "claude-3-opus-20240229",

    "claude-sonnet-4-20250514",

    "claude-opus-4-20250514",

    "claude-3-7-sonnet"
]

# =====================
# 测试模型
# =====================
def test_model(model):

    try:

        client.messages.create(
            model=model,
            max_tokens=5,
            messages=[
                {
                    "role": "user",
                    "content": "hi"
                }
            ]
        )

        return True

    except Exception:
        return False

# =====================
# 首页
# =====================
@app.route("/")
def home():

    available_models = []

    for model in MODEL_CANDIDATES:

        if test_model(model):
            available_models.append(model)

    html = """
    <html>
    <head>

        <title>Claude Model Scanner</title>

        <style>

            body{
                background:#111;
                color:white;
                font-family:Arial;
                padding:40px;
            }

            .card{
                background:#1d1d1d;
                padding:20px;
                margin-bottom:15px;
                border-radius:12px;
            }

            .ok{
                color:#4cff90;
                font-size:20px;
            }

        </style>

    </head>

    <body>

        <h1>🧠 Claude Available Models</h1>
    """

    for model in available_models:

```
