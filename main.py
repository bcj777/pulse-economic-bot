from flask import Flask
from telegram import Bot
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Pulse Economic Bot online"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
