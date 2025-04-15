import streamlit as st
import fitz  # PyMuPDF
import requests

# --- Извлечение текста из PDF ---
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    return "\n".join([page.get_text() for page in doc])

# --- Оценка резюме по ключевым словам ---
def score_resume(text):
    score = 0
    report = []

    checks = [
        ("телефон", 10, "Упоминание телефонных звонков"),
        ("звонк", 10, "Опыт звонков клиентам"),
        ("переговор", 10, "Участие в переговорах"),
        ("продаж", 10, "Опыт продаж"),
        ("клиент", 5, "Работа с клиентами"),
        ("1с", 5, "Опыт с 1С"),
        ("crm", 3, "Работа с CRM-системами"),
        ("внимательн", 5, "Упоминание внимательности"),
        ("детал", 5, "Внимание к деталям"),
        ("удален", 2, "Опыт удаленной работы"),
    ]

    penalties = [
        ("гос", -5, "Опыт в государственных структурах"),
        ("меньше года", -5, "Работа на месте меньше года"),
    ]

    text = text.lower()

    if "рарус" in text and "настоящее время" in text:
        return -999, ["❌ Работает в «Рарус» в настоящее время — автoотказ"]

    for keyword, weight, reason in checks:
        if keyword in text:
            score += weight
            report.append(f"+{weight}: {reason}")

    for keyword, penalty, reason in penalties:
        if keyword in text:
            score += penalty
            report.append(f"{penalty}: {reason}")

    return score, report

# --- Запрос к GPT-4 через OpenRouter ---
def ask_gpt(prompt, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-app-name.streamlit.app",  # замените на ваш Streamlit URL после деплоя
        "X-Title": "Resume Scoring App"
    }

    data = {
        "model": "openai/gpt-4",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Ошибка от API: {response.status_code} - {response.text}"

# --- Интерфейс Streamlit ---
st.set_page_config(page_title="Оценка резюме", layout="centered")
st.title("📄 Оценка резюме для вакансии телефониста")

uploaded_file = st.file_uploader("Загрузите PDF-файл резюме", type="pdf")

if uploaded_file:
    resume_text = extract_text_from_pdf(uploaded_file)
    st.subheader("📝 Извлечённый текст:")
    st.text_area("Текст резюме", resume_text[:3000], height=300)

    score, report = score_resume(resume_text)

    if score == -999:
        st.error("❌ Автоотказ: Кандидат работает в «Рарус» в настоящее время")
    else:
        st.subheader(f"🔢 Итоговая оценка: {score} баллов")

        if score >= 30:
            st.success("✅ Резюме подходит для вакансии (высокое соответствие)")
        elif 15 <= score < 30:
            st.warning("🟡 Частичное соответствие — стоит рассмотреть внимательнее")
        else:
            st.error("❌ Резюме не соответствует требованиям")

        st.subheader("📌 Причины начисления баллов:")
        for line in report:
            st.markdown(f"- {line}")

    st.divider()
    st.subheader("🤖 Задать вопрос ИИ по резюме")
    user_question = st.text_input("Введите вопрос к ИИ")

    if st.button("Спросить у GPT") and user_question.strip():
        openai_api_key = st.secrets["openai"]["openai_api_key"]
        with st.spinner("GPT думает..."):
            ai_response = ask_gpt(f"Вот текст резюме:\n{resume_text}\n\nВопрос: {user_question}", api_key)
            st.markdown("**Ответ:**")
            st.write(ai_response)
else:
    st.info("⬆️ Пожалуйста, загрузите PDF-файл резюме")
