import logging
import datetime
import json
import os

from telegram.ext import (
    ApplicationBuilder, CallbackQueryHandler, MessageHandler,
    ChatMemberHandler, ContextTypes, filters
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = "8056403018:AAGNxC2e81Wt_SSGFaBP9LG_CPCnR2kIYWs"
GROUP_ID = -1000000000000  # заменишь на свой если нужно
DATA_FILE = "user_choices.json"
MESSAGE_ID_FILE = "message_id.json"

def save_message_id(chat_id, message_id):
    with open(MESSAGE_ID_FILE, "w") as f:
        json.dump({"chat_id": chat_id, "message_id": message_id}, f)

def load_message_id():
    if os.path.exists(MESSAGE_ID_FILE):
        with open(MESSAGE_ID_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            else:
                return {"chat_id": GROUP_ID, "message_id": data}
    return None

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


# Загрузка и сохранение данных
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_choices = load_data()


# Получить пользователей по выбору
def get_users_by_choice(choice):
    return [f"@{u}" for u, c in user_choices.items() if c == choice]


# Обновление общего списка в чате
def update_participant_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    message = "📋 *Обновлённый список:*\n\n"
    message += "🧳 4–5 июля: " + ", ".join(get_users_by_choice("4")) + "\n"
    message += "🎉 5–6 июля: " + ", ".join(get_users_by_choice("5")) + "\n"
    message += "🤔 Думают: " + ", ".join(get_users_by_choice("думаю")) + "\n"
    message += "❌ Не едут: " + ", ".join(get_users_by_choice("нет"))

    stored = load_message_id()
    if stored and stored["chat_id"] == chat_id:
        try:
            context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=stored["message_id"],
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print("Ошибка при редактировании:", e)
    else:
        sent = context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        save_message_id(chat_id, sent.message_id)


# Обработка кнопок
def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    choice = query.data
    username = user.username or f"id{user.id}"

    user_choices[username] = choice
    save_data(user_choices)

    query.answer()
    update_participant_message(context, query.message.chat.id)


# Приветственное сообщение с кнопками и текстом
def send_welcome_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    keyboard = [
        [InlineKeyboardButton("🧳 с 4 на 5 июля", callback_data="4")],
        [InlineKeyboardButton("🎉 с 5 на 6 июля", callback_data="5")],
        [InlineKeyboardButton("🤔 Ещё думаю", callback_data="думаю")],
        [InlineKeyboardButton("❌ Не еду", callback_data="нет")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    greeting = """
*Йоу! Съезжаемся на дачу — будет легендарно.*  
Плед, банька, жара, бассейн, шашлычок — короче, полный релакс в лучших традициях.  
Загораем под солнцем, чилим на природе.  
Те, кто был — знают. Те, кто не был — вот шанс всё исправить 🔥  
Зову вас на *свой день рождения*, и хочу, чтобы каждый стал частью этой душевной тусовки!

📍 Где: Бабино-2  
📅 Когда:  
— Приезжай с *вечера 4 на 5 июля* — это формат «2 ночи и полный чилл»  
— Или с *5 на 6 июля* — главная тусовка с субботы на воскресенье  
🎂 День рождения — 6 июля, так что гуляем заранее 🎉

📦 Что взять с собой:  
🩴 Купальник  
🧖 Полотенце  
🧺 Пледик  
🧥 Одежду по погоде  
😄 Главное — хорошее настроение и свободный мозг!

💬 Да, и по классике: как забыть тот легендарный момент, когда Роману сказали, что он «не сможет», — и он *пробил дверь кулаком*, не сказав ни слова.  
Так что будьте добры, *не спорьте с Романом* 😂

👇 Отметься, когда поедешь:"""

    context.bot.send_message(chat_id=chat_id, text=greeting, reply_markup=reply_markup, parse_mode="Markdown")


# Авто-отправка приветствия при добавлении бота в группу
def new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                send_welcome_message(context, update.effective_chat.id)


# Ежедневная проверка и напоминания
def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now().date()

    if today == datetime.date(2025, 7, 3):
        for username, choice in user_choices.items():
            if choice == "4":
                try:
                    context.bot.send_message(
                        chat_id=f"@{username}",
                        text="Йоу! 🎉 Завтра уже старт — ты выбрал ехать с 4 на 5 июля, и это будет главная тусовка на две ночи! Не забудь взять нужное, выспаться и оставить все заботы дома. До встречи под шум деревьев 🌳"
                    )


                except Exception as e:
                    print(f"Ошибка отправки @{username}: {e}")

    if today == datetime.date(2025, 7, 4):
        for username, choice in user_choices.items():
            if choice == "5":
                try:
                    context.bot.send_message(
                        chat_id=f"@{username}",
                        text="Йоу! 🎉 Завтра уже старт — ты выбрал ехать с 5 на 6 июля, и это будет главная тусовка! Не забудь взять нужное, выспаться и оставить все заботы дома. До встречи под шум деревьев и всплеск реки 🌊"
                    )
                except Exception as e:
                    print(f"Ошибка отправки @{username}: {e}")


# Запуск бота
from telegram.ext import ApplicationBuilder

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member))
    application.add_handler(ChatMemberHandler(new_chat_member, chat_member_types=["my_chat_member"]))

    job_queue = application.job_queue
    job_queue.run_daily(send_reminders, time=datetime.time(hour=12, minute=0))

    application.run_polling()


if __name__ == "__main__":
    main()
