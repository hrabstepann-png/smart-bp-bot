import telebot
import openai
import time
import re

# === ВСТАВ СВОЇ ДАНІ СЮДИ ===
TG_TOKEN = "8543702363:AAHoVTSOoMKEtakGeS7BBd-rg3C41jACKdY"
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
ASSISTANT_ID = "ВСТАВ_СВІЙ_ASSISTANT_ID"
# ============================

# Ініціалізація клієнтів
bot = telebot.TeleBot(TG_TOKEN)
client = openai.Client(api_key=OPENAI_API_KEY)

# Словник для збереження пам'яті: {telegram_id: thread_id_openai}
user_threads = {}

# Обробка команд /start та /clear (Очищення пам'яті)
@bot.message_handler(commands=['start', 'clear'])
def handle_start_clear(message):
    user_id = message.from_user.id
    
    # Створюємо абсолютно новий thread в OpenAI для чистого аркуша
    thread = client.beta.threads.create()
    user_threads[user_id] = thread.id
    
    welcome_text = (
        "👋 **Вітаю в корпоративній базі знань БП!**\n\n"
        "Я ваш AI-асистент. Я пам'ятаю контекст нашої поточної розмови, тому ви можете задавати мені уточнюючі питання.\n\n"
        "🧹 Якщо ви хочете забути поточну тему і почати діалог **з чистого аркуша**, просто надішліть команду /clear\n\n"
        "💡 **Приклади запитань, які можна поставити:**\n"
        "• _Як правильно оформити повернення товару від клієнта?_\n"
        "• _Які документи потрібні для прийому техніки в сервіс?_"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

# Обробка текстових запитів користувача
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    prompt = message.text

    # Якщо користувач пише вперше і в нього немає thread_id — створюємо його
    if user_id not in user_threads:
        thread = client.beta.threads.create()
        user_threads[user_id] = thread.id

    thread_id = user_threads[user_id]

    # Надсилаємо тимчасове повідомлення статусу
    status_msg = bot.reply_to(message, "⏳ _Аналізую базу знань компанії..._", parse_mode="Markdown")

    try:
        # 1. Додаємо повідомлення користувача в його індивідуальний потік (thread)
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt
        )

        # 2. Запускаємо Асистента
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        # 3. Очікуємо на відповідь від OpenAI
        while run.status in ['queued', 'in_progress']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

        # 4. Коли запит виконано успішно
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            assistant_response = messages.data[0].content[0].text.value
            
            # Вирізаємо технічні посилання OpenAI типу 【4:1†source】
            assistant_response = re.sub(r'【.*?】', '', assistant_response)

            # Замінюємо текст статус-повідомлення на фінальну відповідь
            bot.edit_message_text(
                chat_id=message.chat.id, 
                message_id=status_msg.message_id, 
                text=assistant_response
            )
        else:
            bot.edit_message_text(
                chat_id=message.chat.id, 
                message_id=status_msg.message_id, 
                text="❌ Помилка обробки в OpenAI. Перевірте статус Асистента."
            )

    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id, 
            message_id=status_msg.message_id, 
            text=f"❌ Сталася технічна помилка: {str(e)}"
        )

# Безперервний запуск бота
if __name__ == '__main__':
    print("Бот успішно запущений і готовий до роботи...")
    bot.infinity_polling()
