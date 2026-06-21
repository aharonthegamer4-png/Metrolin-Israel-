from flask import Flask
from threading import Thread

# הגדרת שרת ה-Flask עבור Render
app = Flask('')

@app.route('/')
def home():
    return "Bot is online and running 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """פונקציה שמפעילה את שרת האינטרנט ב-Thread נפרד"""
    t = Thread(target=run)
    t.start()
