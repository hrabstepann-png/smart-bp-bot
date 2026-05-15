import streamlit as st
import openai
import time

# === ВСТАВ СВОЇ КЛЮЧІ ТУТ ===
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
ASSISTANT_ID = st.secrets["ASSISTANT_ID"]
# ============================

client = openai.Client(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="База знань БП", page_icon="📚")
# Відображення логотипу
st.image("logo.png", width=250)
# Приховуємо стандартні елементи інтерфейсу Streamlit (GitHub, меню, футер)
hide_ui_style = """
<style>
[data-testid="stToolbar"] {visibility: hidden !important;}
header {visibility: hidden !important;}
footer {visibility: hidden !important;}
</style>
"""
st.markdown(hide_ui_style, unsafe_allow_html=True)
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

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Напишіть питання щодо бізнес-процесу..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
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
            
            if run.status == 'completed':
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
