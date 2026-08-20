from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot está online"

def run():
    # O Render usa a porta 10000 por padrão, mas mapeia o 0.0.0.0 automaticamente
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()