import streamlit as st
import openai
import time

# === ВСТАВ СВОЇ КЛЮЧІ ТУТ ===
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
ASSISTANT_ID = st.secrets["ASSISTANT_ID"]
# ============================

client = openai.Client(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="База знань БП", page_icon="📚" layout="wide")
# Відображення логотипу
st.image("logo.png", width=250)
# Приховуємо стандартні елементи інтерфейсу Streamlit (GitHub, меню, футер)
# Сучасний дизайн: приховування UI, тіні, картки та виразне поле вводу
modern_css = """
<style>
/* Приховуємо стандартні елементи */
[data-testid="stToolbar"] {visibility: hidden !important;}
header {visibility: hidden !important;}
footer {visibility: hidden !important;}

/* Робимо поле вводу виразнішим (заокруглення і тінь) */
[data-testid="stChatInput"] {
    border: 2px solid #2196F3 !important;
    border-radius: 15px !important;
    box-shadow: 0px 8px 20px rgba(33, 150, 243, 0.15) !important;
}

/* Оформлюємо повідомлення як сучасні картки */
[data-testid="stChatMessage"] {
    background-color: #ffffff;
    border-radius: 15px;
    padding: 15px;
    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
    margin-bottom: 15px;
    border: 1px solid #f0f2f6;
}
</style>
"""
st.markdown(modern_css, unsafe_allow_html=True)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Вхід у систему")
    email_input = st.text_input("Введіть ваш Email (для тесту test@gmail.com):")
    
    if st.button("Увійти"):
        if email_input == "test@gmail.com":
            st.session_state.authenticated = True
            st.session_state.user_email = email_input
            st.rerun()
        else:
            st.error("Доступ заборонено. Невірний email.")
else:
    st.title("📚 AI Консультант БП")
    st.caption(f"Ви увійшли як: {st.session_state.user_email}")
    
    if st.sidebar.button("Вийти"):
        st.session_state.authenticated = False
        st.rerun()

    # Створюємо сесію розмови з OpenAI
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    if "messages" not in st.session_state:
        st.session_state.messages = []
# --- ПОЧАТОК НОВОГО БЛОКУ: ЕКРАН ПРИВІТАННЯ ---
    if len(st.session_state.messages) == 0:
        st.markdown("### 👋 Вітаю в базі знань!")
        st.info("Я ваш корпоративний AI-асистент. Моя ціль — допомагати вам швидко знаходити потрібні інструкції та відповіді по наших бізнес-процесах.")
        
        st.markdown("**💡 Приклади запитань, які ви можете мені поставити:**")
        st.markdown("> *Як правильно оформити повернення товару від клієнта?*")
        st.markdown("> *Які документи потрібні для прийому телефону в сервісний центр?*")
        st.markdown("> *Який алгоритм дій при роботі з запереченнями?*")
# --- КІНЕЦЬ НОВОГО БЛОКУ ---
for msg in st.session_state.messages:
        # Визначаємо аватарку: логотип для бота, силует для людини
        avatar_img = "logo.png" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar_img):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Напишіть питання щодо бізнес-процесу..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Відправка запиту в OpenAI
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID
        )

        with st.spinner("Аналізую базу знань..."):
            while run.status in ['queued', 'in_progress']:
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )
            
            if run.status == 'completed':with st.chat_message("assistant", avatar="logo.png"):
                    st.markdown(assistant_response)
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                # Беремо останню відповідь
                assistant_response = messages.data[0].content[0].text.value
                
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                with st.chat_message("assistant"):
                    st.markdown(assistant_response)
            else:
                st.error("Виникла помилка. Перевірте API ключі та баланс.")
