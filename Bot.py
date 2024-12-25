import random
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Словарь случайных сообщений для команды /start
random_messages = {
    1: "Привет! Как настроение?",
    2: "Надеюсь, у тебя отличный день!",
    3: "Давай начнем что-нибудь интересное!",
}

# Стоп-слово для завершения игры
STOP_WORD = "стоп"


# Функция для загрузки сообщений из файла
def load_messages_from_file(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]


# Загрузка сообщений из файла
file_messages = load_messages_from_file("messages.txt")


# Команда /start - отправляет случайное сообщение из словаря
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = random.choice(list(random_messages.values()))
    await update.message.reply_text(message)


# Периодическая отправка случайного сообщения из файла
async def send_random_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    if file_messages:
        message = random.choice(file_messages)
        await context.bot.send_message(chat_id=chat_id, text=message)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Файл сообщений пуст.")


# Команда для запуска таймера
async def start_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    context.job_queue.run_repeating(send_random_message, interval=10, first=0, chat_id=chat_id, name=str(chat_id))
    await update.message.reply_text("Периодическая отправка сообщений начата.")


# Команда для остановки таймера
async def stop_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_jobs = context.job_queue.get_jobs_by_name(str(update.message.chat_id))
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()
        await update.message.reply_text("Таймер остановлен.")
    else:
        await update.message.reply_text("Таймер не запущен.")


# Команда для просмотра содержимого файла
async def view_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = "messages.txt"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()
        await update.message.reply_text(content if content else "Файл пуст.")
    else:
        await update.message.reply_text("Файл не найден.")


# Команда для добавления сообщения в файл
async def add_to_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = "messages.txt"
    message = " ".join(context.args)
    if message:
        with open(filename, "a", encoding="utf-8") as file:
            file.write(message + "\n")
        await update.message.reply_text("Сообщение добавлено в файл.")
    else:
        await update.message.reply_text("Пожалуйста, укажите сообщение для добавления.")


# Игра со стоп-словом
async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == STOP_WORD:
        await update.message.reply_text("Игра окончена. Вы написали стоп-слово!")
    else:
        await update.message.reply_text(
            f"Вы написали: {update.message.text}. Напишите '{STOP_WORD}' для завершения игры.")


# Сохранение истории переписки в файл
async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_filename = f"history_{date_str}.txt"
    user = update.message.from_user
    log_entry = f"{datetime.now().strftime('%H:%M:%S')} - {user.username or user.first_name}: {update.message.text}\n"

    if update.message.text.strip():
        with open(log_filename, "a", encoding="utf-8") as file:
            file.write(log_entry)


# Основная функция для запуска бота
def main():
    # Получаем токен из переменной окружения
    token = os.getenv("7648569681:AAGD1vpOYv-sHV7tCPGRie8l6kgro6nEQJk")
    if not token:
        print("Ошибка: не найден токен бота в переменной окружения 'TELEGRAM_TOKEN'.")
        return

    # Инициализация приложения
    application = Application.builder().token(token).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("start_timer", start_timer))
    application.add_handler(CommandHandler("stop_timer", stop_timer))
    application.add_handler(CommandHandler("view_file", view_file))
    application.add_handler(CommandHandler("add_to_file", add_to_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, game))

    # Запускаем бота
    application.run_polling()


if __name__ == "__main__":
    main()
