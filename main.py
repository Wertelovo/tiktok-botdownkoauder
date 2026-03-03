import os
import telebot
import yt_dlp
import requests
from flask import Flask, request
from threading import Thread
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise Exception("Токен не найден!")

bot = telebot.TeleBot(TOKEN, threaded=True)  # ← Включить потоки
app = Flask(__name__)

RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
IS_ON_RENDER = RENDER_EXTERNAL_URL is not None

# ================== ОБРАБОТЧИКИ TELEGRAM ==================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне ссылку на TikTok 🎬")

@bot.message_handler(content_types=['text'])
def handle_link(message):
    link = message.text
    if 'tiktok.com' not in link:
        bot.reply_to(message, "Похоже, это не ссылка на TikTok.")
        return
    
    status_msg = bot.reply_to(message, "⏳ Скачиваю видео...")
    
    # ← Запускаем загрузку в отдельном потоке
    Thread(target=download_and_send, args=(message, status_msg, link)).start()

def download_and_send(message, status_msg, link):
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(id)s.%(ext)s',
            'noplaylist': True,
            'no_warnings': True,
            'socket_timeout': 30,  # ← Таймауты!
            'retries': 3,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="📤 Отправляю видео..."
            )
            
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption="🎬 Готово!", timeout=120)
            
            os.remove(filename)
            bot.delete_message(message.chat.id, status_msg.message_id)
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)[:100]}")
        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except:
            pass

# ================== FLASK-МАРШРУТЫ ==================
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
        # ← НЕ устанавливаем webhook автоматически!
        WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}/webhook"
        print(f"🚀 Запуск на Render. Webhook URL: {WEBHOOK_URL}")
        print(f"⚠️ Установите webhook вручную: https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
        # app.run() не нужен - Gunicorn запускает сервер
    else:
        bot.remove_webhook()
        print("🏠 Запуск локально (Polling)...")
        bot.infinity_polling()