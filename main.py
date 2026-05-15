import os
import requests
from flask import Flask

app = Flask(**name**)

API_KEY = os.environ.get("ANTHROPIC_API_KEY")

@app.route("/")
def home():

```
headers = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01"
}

response = requests.get(
    "https://api.anthropic.com/v1/models",
    headers=headers
)

data = response.json()

html = """
<html>

<head>

    <title>Claude Models</title>

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

        .name{
            color:#4cff90;
            font-size:20px;
            font-weight:bold;
        }

    </style>

</head>

<body>

    <h1>🧠 Claude Available Models</h1>
"""

if "data" in data:

    for model in data["data"]:

        model_id = model.get("id", "unknown")

        display_name = model.get("display_name", "")

        html += f"""

        <div class="card">

            <div class="name">{model_id}</div>

            <div>{display_name}</div>

        </div>

        """

else:

    html += f"""

    <div class="card">

        ❌ API ERROR

        <pre>{data}</pre>

    </div>

    """

html += """

</body>

</html>
"""

return html
```

if **name** == "**main**":

```
port = int(os.environ.get("PORT", 8080))

app.run(
    host="0.0.0.0",
    port=port
)
```
