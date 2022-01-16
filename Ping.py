from flask import Flask
from threading import Thread

bot = Flask('')
@bot.route('/')
def home():
  return "I am on"

def run():
  bot.run(host='0.0.0.0',port=8080)

def _ping():
  alive = Thread(target=run)
  alive.start()
