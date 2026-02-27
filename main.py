import os
import telebot
import yt_dlp
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise Exception("Токен не найден!")

bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)

# Определяем режим запуска
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
IS_ON_RENDER = RENDER_EXTERNAL_URL is not None

# ================== ОБРАБОТЧИКИ ==================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне ссылку на TikTok 🎬")

@bot.message_handler(content_types=['text'])
def handle_link(message):
    # ... твой код обработки ...
    pass

# ================== ВЕБХУК ДЛЯ TELEGRAM ==================

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return '', 200

@app.route('/')
def index():
    return 'Bot is running!', 200

# ================== ЗАПУСК ==================

if __name__ == '__main__':
    if IS_ON_RENDER:
        # 🌐 Режим Render
        WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}/webhook"
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"🚀 Запуск на Render. Webhook: {WEBHOOK_URL}")
        # Запускаем Flask-сервер
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    
    else:
        # 🏠 Локальный режим (Polling)
        bot.remove_webhook()
        print("🏠 Запуск локально (Polling)...")
        bot.infinity_polling()