import os
import telebot
import yt_dlp
import requests
from flask import Flask, request
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    raise Exception("Токен не найден! Проверь .env или настройки Render")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Определяем, где запущен бот
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
IS_ON_RENDER = RENDER_EXTERNAL_URL is not None

# ================== ОБРАБОТЧИКИ ==================

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

    try:
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': '%(id)s.%(ext)s',
            'noplaylist': True,
            'impersonate': 'chrome:120',
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
            bot.send_video(message.chat.id, video, caption="🎬 Готово!")
        
        os.remove(filename)
        bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except:
            pass

# ================== ЗАПУСК ==================

if __name__ == '__main__':
    if IS_ON_RENDER:
        # 🌐 Режим для Render (Webhook)
        WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}/webhook"
        bot.set_webhook(url=WEBHOOK_URL)
        
        @app.route('/webhook', methods=['POST'])
        def webhook():
            update = request.get_json()
            bot.process_new_updates([telebot.types.Update.de_json(update)])
            return '', 200
        
        @app.route('/')
        def index():
            return 'Bot is running!', 200
        
        print(f"🚀 Запуск на Render. Webhook: {WEBHOOK_URL}")
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    
    else:
        # 🏠 Режим для локального запуска (Polling)
        bot.remove_webhook()  # Отключаем вебхук для локальной работы
        print("🏠 Запуск локально (Polling)...")
        print("Бот готов к работе!")
        bot.infinity_polling()