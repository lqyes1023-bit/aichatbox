import os
from flask import Flask

app = Flask(**name**)

@app.route("/")
def home():
return """ <h1>Claude Scanner Running 💚</h1> <p>Cloud Run 已成功启动</p>
"""

if **name** == "**main**":


port = int(os.environ.get("PORT", 8080))

app.run(
    host="0.0.0.0",
    port=port
)

