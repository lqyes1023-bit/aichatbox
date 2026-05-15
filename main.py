```python
import os
from flask import Flask
import anthropic

app = Flask(__name__)

# =====================
# API KEY
# =====================
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY
)

# =====================
# 要测试的模型
# =====================
MODELS = [

    "claude-3-5-sonnet-latest",
    "claude-3-5-sonnet-20241022",

    "claude-3-opus-latest",

    "claude-3-haiku-20240307",

    "claude-3-sonnet-20240229",

    "claude-3-opus-20240229"
]

# =====================
# TEST MODEL
# =====================
def test_model(model_name):

    try:

        response = client.messages.create(
            model=model_name,
            max_tokens=20,
            messages=[
                {
                    "role": "user",
                    "content": "hello"
                }
            ]
        )

        text = response.content[0].text

        return {
            "status": "✅ AVAILABLE",
            "reply": text
        }

    except Exception as e:

        return {
            "status": "❌ ERROR",
            "reply": str(e)
        }

# =====================
# HOME PAGE
# =====================
@app.route("/")
def home():

    html = """
    <html>
    <head>
        <title>Claude Model Detector</title>

        <style>
            body{
                background:#111;
                color:#eee;
                font-family:Arial;
                padding:40px;
            }

            .card{
                background:#1c1c1c;
                padding:20px;
                margin-bottom:20px;
                border-radius:12px;
            }

            .ok{
                color:#4cff90;
            }

            .bad{
                color:#ff5e5e;
            }

            pre{
                white-space:pre-wrap;
            }
        </style>
    </head>

    <body>

        <h1>🧠 Claude API Detector</h1>

    """

    for model in MODELS:

        result = test_model(model)

        ok = "ok" if "AVAILABLE" in result["status"] else "bad"

        html += f"""

        <div class="card">

            <h2>{model}</h2>

            <p class="{ok}">
                {result["status"]}
            </p>

            <pre>{result["reply"]}</pre>

        </div>

        """

    html += """
    </body>
    </html>
    """

    return html

# =====================
# RUN
# =====================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port
    )
```
