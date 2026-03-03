import os
import telebot
import yt_dlp
import json
import logging
from telebot import types
from dotenv import load_dotenv

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise Exception("Токен не найден!")

# Инициализация бота
bot = telebot.TeleBot(TOKEN, threaded=False, skip_pending=True)

# ================== СТАТИСТИКА ==================

STATS_FILE = 'stats.json'

def load_stats():
    """Загрузка статистики из файла"""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {'total': 0, 'users': {}}

def save_stats(stats):
    """Сохранение статистики в файл"""
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# Загружаем статистику при старте
stats = load_stats()
logger.info(f"📊 Статистика загружена: всего {stats['total']} скачиваний")

# ================== КЛАВИАТУРЫ ==================

def get_main_keyboard():
    """Главное меню с кнопками"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn1 = types.KeyboardButton("📥 Скачать видео")
    btn2 = types.KeyboardButton("📊 Моя статистика")
    btn3 = types.KeyboardButton("ℹ️ Помощь")
    markup.add(btn1)
    markup.add(btn2, btn3)
    return markup

def get_back_keyboard():
    """Кнопка «Назад»"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("↩️ Назад в меню")
    markup.add(btn)
    return markup

# ================== ОБРАБОТЧИКИ ==================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветственное сообщение"""
    user_name = message.from_user.first_name
    text = (
        f"👋 Привет, {user_name}!\n\n"
        "Я бот для скачивания видео из TikTok 🎬\n\n"
        "Что я умею:\n"
        "• Скачивать видео по ссылке\n"
        "• Показывать статистику скачиваний\n"
        "• Работать быстро и стабильно\n\n"
        "Выбери действие в меню ниже 👇"
    )
    bot.reply_to(message, text, reply_markup=get_main_keyboard())

@bot.message_handler(commands=['help'])
def send_help(message):
    """Справка"""
    text = (
        "ℹ️ **Помощь**\n\n"
        "**Как скачать видео:**\n"
        "1. Скопируй ссылку на видео из TikTok\n"
        "2. Отправь ссылку мне\n"
        "3. Подожди немного — я пришлю видео\n\n"
        "**Команды:**\n"
        "/start — Главное меню\n"
        "/help — Эта справка\n"
        "/stats — Твоя статистика\n\n"
        "Нажми «↩️ Назад в меню», чтобы вернуться."
    )
    bot.reply_to(message, text, reply_markup=get_back_keyboard(), parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def send_stats(message):
    """Показать статистику"""
    user_id = str(message.chat.id)
    user_downloads = stats['users'].get(user_id, 0)
    total = stats['total']
    
    text = (
        f"📊 **Твоя статистика**\n\n"
        f"Ты скачал: **{user_downloads}** видео\n"
        f"Всего скачано: **{total}** видео\n\n"
        "Так держать! 🎉"
    )
    bot.reply_to(message, text, reply_markup=get_back_keyboard(), parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Обработка текстовых сообщений и кнопок"""
    text = message.text
    
    # Кнопка «Назад в меню»
    if text == "↩️ Назад в меню":
        send_welcome(message)
        return
    
    # Кнопка «Моя статистика»
    if text == "📊 Моя статистика":
        send_stats(message)
        return
    
    # Кнопка «Помощь»
    if text == "ℹ️ Помощь":
        send_help(message)
        return
    
    # Кнопка «Скачать видео» — просим ссылку
    if text == "📥 Скачать видео":
        bot.reply_to(
            message,
            " Отправь мне ссылку на TikTok\n(или просто вставь ссылку)",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Проверяем, есть ли ссылка на TikTok
    if 'tiktok.com' in text or 'vt.tiktok.com' in text:
        process_tiktok_link(message, text)
    else:
        bot.reply_to(
            message,
            "❌ Не похоже на ссылку TikTok.\n\n"
            "Отправь правильную ссылку или выбери действие в меню.",
            reply_markup=get_main_keyboard()
        )

def process_tiktok_link(message, link):
    """Скачивание видео из TikTok"""
    status_msg = bot.reply_to(message, "⏳ Скачиваю видео...", reply_markup=get_back_keyboard())
    
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
            bot.send_video(message.chat.id, video, caption="🎬 Готово! Приятного просмотра!")
        
        # Обновляем статистику
        user_id = str(message.chat.id)
        stats['total'] += 1
        stats['users'][user_id] = stats['users'].get(user_id, 0) + 1
        save_stats(stats)
        
        logger.info(f"✅ Видео скачано. Всего: {stats['total']}, Пользователь {user_id}: {stats['users'][user_id]}")
        
        os.remove(filename)
        bot.delete_message(message.chat.id, status_msg.message_id)
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        bot.reply_to(message, f"❌ Ошибка при скачивании: {type(e).__name__}\nПопробуй другую ссылку.", reply_markup=get_main_keyboard())
        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except:
            pass

# ================== ЗАПУСК ==================

if __name__ == '__main__':
    logger.info("🏠 Запуск бота в режиме Polling...")
    bot.remove_webhook()
    bot.infinity_polling()