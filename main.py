import os
import telebot
import yt_dlp
from flask import Flask, request
from dotenv import load_dotenv
import logging

# Настройка логов (чтобы видеть всё в консоли Render)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise Exception("Токен не найден!")

# Инициализация бота
bot = telebot.TeleBot(TOKEN, threaded=False, skip_pending=True)
app = Flask(__name__)

# ================== ОБРАБОТЧИКИ ==================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    logger.info(f"📩 Команда /start от пользователя {message.chat.id}")
    bot.reply_to(message, "Привет! Отправь мне ссылку на TikTok 🎬")

@bot.message_handler(content_types=['text'])
def handle_link(message):
    link = message.text
    logger.info(f"📩 Сообщение от {message.chat.id}: {link}")
    
    if 'tiktok.com' not in link:
        bot.reply_to(message, "Похоже, это не ссылка на TikTok.")
        return

    status_msg = bot.reply_to(message, "⏳ Скачиваю видео...")

    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'noplaylist': True,
            'no_warnings': True,
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
        logger.error(f"❌ Ошибка: {e}")
        bot.reply_to(message, f"❌ Ошибка: {type(e).__name__}")
        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except:
            pass

# ================== ВЕБХУК ==================

@app.route('/webhook', methods=['POST'])
def webhook():
    # Логируем входящий запрос
    logger.info("📡 Получен запрос от Telegram")
    
    update = request.get_json()
    if update:
        logger.info(f"📦 Данные обновления: {update}")
        bot.process_new_updates([telebot.types.Update.de_json(update)])
    else:
        logger.warning("⚠️ Пустой запрос от Telegram")
    
    return '', 200

@app.route('/')
def index():
    return 'Bot is running!', 200

# ================== ЗАПУСК ==================

if __name__ == '__main__':
    logger.info("🏠 Запуск в режиме Polling...")
    bot.remove_webhook()
    bot.infinity_polling()