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

# ================== ОБРАБОТЧИКИ TELEGRAM ==================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне ссылку на TikTok 🎬")

@bot.message_handler(content_types=['text'])
def handle_link(message):
    import traceback  # Добавь импорт в начале функции
    
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
        # 🔴 ВОТ ЭТО ДОБАВЬ — ошибка появится в логах Render
        print(f"❌ FULL ERROR: {traceback.format_exc()}")
        print(f"❌ SHORT ERROR: {str(e)}")
        
        # Пользователю показываем упрощённое сообщение
        error_text = str(e).lower()
        if "blocked" in error_text:
            bot.reply_to(message, "❌ TikTok блокирует запрос. Попробуй другую ссылку.")
        elif "private" in error_text:
            bot.reply_to(message, "❌ Видео из закрытого аккаунта.")
        else:
            bot.reply_to(message, f"❌ Ошибка: {type(e).__name__}")
        
        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except:
            pass

# ================== FLASK-МАРШРУТЫ (всегда на верхнем уровне!) ==================

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик вебхука от Telegram"""
    update = request.get_json()
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return '', 200

@app.route('/')
def index():
    """Проверка, что сервер работает"""
    return 'Bot is running!', 200

# ================== ЗАПУСК ==================

if __name__ == '__main__':
    if IS_ON_RENDER:
        # 🌐 Режим Render: устанавливаем вебхук и запускаем сервер
        WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}/webhook"
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"🚀 Запуск на Render. Webhook: {WEBHOOK_URL}")
        # app.run() здесь не используется, так как на Render запускает Gunicorn
    else:
        # 🏠 Локальный режим: отключаем вебхук и запускаем polling
        bot.remove_webhook()
        print("🏠 Запуск локально (Polling)...")
        bot.infinity_polling()