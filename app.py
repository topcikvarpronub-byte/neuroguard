import sqlite3
from datetime import date
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(
    page_title="NeuroGuard: Трекер восстановления и нагрузки",
    page_icon="⚡",
    layout="wide"
)

# --- 2. БАЗА ДАННЫХ SQLITE ---
def init_db():
    conn = sqlite3.connect("recovery_tracker.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT UNIQUE,
            sleep_hours REAL,
            sleep_quality INTEGER,
            study_hours REAL,
            eye_strain INTEGER,
            training_type TEXT,
            training_intensity INTEGER,
            head_impact INTEGER,
            readiness_score INTEGER,
            ai_advice TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_log(data):
    conn = sqlite3.connect("recovery_tracker.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO daily_logs (
            log_date, sleep_hours, sleep_quality, study_hours,
            eye_strain, training_type, training_intensity,
            head_impact, readiness_score, ai_advice
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

def load_logs():
    conn = sqlite3.connect("recovery_tracker.db")
    df = pd.read_sql_query("SELECT * FROM daily_logs ORDER BY log_date DESC", conn)
    conn.close()
    return df

# --- 3. МАТЕМАТИЧЕСКАЯ МОДЕЛЬ (0-100%) ---
def calculate_readiness(sleep_h, sleep_q, study_h, eye_strain, train_int, head_impact):
    sleep_recovery = min(sleep_h / 8.0, 1.15) * 60 + (sleep_q / 10.0) * 40
    cognitive_penalty = study_h * 2.0
    eye_penalty = max(0, (eye_strain - 1) * 3.8)
    physical_penalty = train_int * 2.2
    impact_penalty = 25 if head_impact else 0
    
    score = sleep_recovery - (cognitive_penalty + eye_penalty + physical_penalty + impact_penalty)
    return max(0, min(100, int(round(score))))

init_db()
df_logs = load_logs()

# --- 4. САЙДБАР И ТЁМНАЯ ТЕМА ---
with st.sidebar:
    st.header("🎨 Интерфейс и ИИ")
    dark_mode = st.toggle("🌙 Тёмная тема (Eye-Safe)", value=True)
    st.divider()
    st.markdown(
        "**Профиль мониторинга:**\n"
        "* 📚 Учеба: 10 класс (ЕГЭ / Код)\n"
        "* 🥋 Спорт: Единоборства и ОФП\n"
        "* 👀 Фокус: Защита сетчатки и ЦНС"
    )

if dark_mode:
    st.markdown("""
        <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #0d1117 !important;
            color: #c9d1d9 !important;
        }
        [data-testid="stSidebar"] {
            background-color: #161b22 !important;
            border-right: 1px solid #30363d !important;
        }
        h1, h2, h3, h4, p, span, label, .stMarkdown, [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
            color: #e6edf3 !important;
        }
        div[data-baseweb="select"] > div, input, textarea {
            background-color: #21262d !important;
            color: #e6edf3 !important;
            border: 1px solid #30363d !important;
        }
        .status-box {
            padding: 12px 16px;
            border-radius: 8px;
            font-weight: 600;
            margin-bottom: 15px;
            border: 1px solid #30363d;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .status-box {
            padding: 12px 16px;
            border-radius: 8px;
            font-weight: 600;
            margin-bottom: 15px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 5. ГЛАВНЫЙ ЭКРАН ---
st.title("⚡ NeuroGuard: Мониторинг нагрузки и восстановления")
st.write("Контроль когнитивного ресурса, зрительного утомления и физической готовности.")

col_input, col_result = st.columns([1.1, 1])

with col_input:
    st.subheader("📊 Показатели за день")
    
    log_date = st.date_input("Дата записи", value=date.today())
    
    c1, c2 = st.columns(2)
    with c1:
        sleep_hours = st.slider("Часы сна", 0.0, 12.0, 7.5, 0.5)
        study_hours = st.slider("Учеба и экраны (часы)", 0.0, 14.0, 5.0, 0.5)
        training_type = st.selectbox(
            "Тип физической нагрузки",
            ["Отдых", "ОФП / Турники / Бег", "Техника в воздух / Лапы (без контакта)", "Спарринги / Полный контакт"]
        )
    with c2:
        sleep_quality = st.slider("Качество сна (1–10)", 1, 10, 8)
        eye_strain = st.slider("Усталость / боль в глазах (1–10)", 1, 10, 3)
        
        is_rest = (training_type == "Отдых")
        training_intensity = st.slider(
            "Тяжесть тренировки (0–10)",
            0, 10,
            value=0 if is_rest else 5,
            disabled=is_rest
        )

    head_impact = st.checkbox("Были пропущенные удары в голову или резкое натуживание")
    analyze_btn = st.button("🚀 Рассчитать индекс и сохранить день", use_container_width=True, type="primary")

with col_result:
    st.subheader("🧠 Вердикт системы")
    
    current_score = calculate_readiness(
        sleep_hours, sleep_quality, study_hours, eye_strain, training_intensity, head_impact
    )
    
    score_delta = None
    if not df_logs.empty:
        last_score = int(df_logs.iloc[0]["readiness_score"])
        score_delta = f"{current_score - last_score}% к прошлой записи"

    st.metric(
        label="Индекс готовности организма (Readiness Score)",
        value=f"{current_score}%",
        delta=score_delta
    )
    st.progress(current_score / 100)

    if current_score >= 70 and eye_strain <= 5 and not head_impact:
        st.markdown('<div class="status-box" style="background-color: rgba(46, 160, 67, 0.2); color: #3fb950;">🟢 Оптимальная готовность: ресурс в норме</div>', unsafe_allow_html=True)
    elif current_score >= 45 and eye_strain <= 7 and not head_impact:
        st.markdown('<div class="status-box" style="background-color: rgba(210, 153, 34, 0.2); color: #d29922;">🟡 Умеренное утомление: дозируй экран и спорт</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-box" style="background-color: rgba(248, 81, 73, 0.2); color: #f85149;">🔴 Перегрузка / Риск для глаз: нужен режим восстановления!</div>', unsafe_allow_html=True)

    if analyze_btn:
        ai_advice = None
        
        # Проверяем, есть ли защищенный ключ в настройках Streamlit Cloud или локально в st.secrets
        api_key = None
        try:
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

        if api_key:
            with st.spinner("Нейросеть анализирует показатели..."):
                try:
                    client = genai.Client(api_key=api_key)
                    prompt = f"""
                    Ты — спортивный врач-офтальмолог и эксперт по биохакингу.
                    Проанализируй показатели старшеклассника (готовится к ЕГЭ, занимается каратэ, высокая дальнозоркость, риск для сетчатки):
                    - Сон: {sleep_hours} ч (качество {sleep_quality}/10)
                    - Работа за экраном / учеба: {study_hours} ч
                    - Усталость/боль в глазах: {eye_strain}/10
                    - Тренировка: {training_type} (интенсивность {training_intensity}/10)
                    - Удары в голову / натуживание: {"Да" if head_impact else "Нет"}
                    - Индекс готовности: {current_score}%

                    Выдай краткий план действий на завтра в 3 пунктах:
                    1. СПОРТ (что можно, что запрещено).
                    2. УЧЕБА И ЭКРАНЫ (тайминги).
                    3. ЗАЩИТА ЗРЕНИЯ И ВОССТАНОВЛЕНИЕ.
                    Пиши четко, по делу, без воды.
                    """
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.3)
                    )
                    ai_advice = response.text
                except Exception as e:
                    ai_advice = None

        # Если ключа нет или ИИ не ответил — включаем экспертную экспертную логику
        if not ai_advice:
            advice_parts = []
            if eye_strain >= 6 or head_impact:
                advice_parts.append("⚠️ **Зрение:** Высокий риск перегрузки сетчатки и аккомодации. Полностью исключи спарринги, резкие натуживания и сократи экранное время.")
            else:
                advice_parts.append("👀 **Зрение:** Нагрузка в пределах нормы, но при работе с кодом соблюдай правило 20-20-20 (каждые 20 минут смотри вдаль).")
            
            if current_score < 50:
                advice_parts.append("🔋 **Режим:** ЦНС перегружена. Завтра только легкая разминка и сон минимум 8 часов.")
            else:
                advice_parts.append("💪 **Режим:** Хороший тонус. Можно продуктивно ботать и делать ОФП / технику в воздух без контакта в голову.")
            ai_advice = "\n\n".join(advice_parts)

        save_log((
            str(log_date), sleep_hours, sleep_quality, study_hours,
            eye_strain, training_type, training_intensity,
            int(head_impact), current_score, ai_advice
        ))
        df_logs = load_logs()
        st.success("Запись за день сохранена!")
        st.markdown("### 📋 Рекомендация")
        st.info(ai_advice)

# --- 6. ИСТОРИЯ, СТАТИСТИКА И ГРАФИКИ ---
st.divider()
st.subheader("📈 Динамика состояния и аналитика")

if not df_logs.empty:
    # Блок мини-статистики (метрики за все время в базе)
    m1, m2, m3 = st.columns(3)
    m1.metric("Средний сон", f"{df_logs['sleep_hours'].mean():.1f} ч")
    m2.metric("Средняя усталость глаз", f"{df_logs['eye_strain'].mean():.1f} / 10")
    m3.metric("Средний индекс готовности", f"{df_logs['readiness_score'].mean():.0f}%")

    tab1, tab2 = st.tabs(["Графики нагрузки", "База записей"])
    
    with tab1:
        chart_df = df_logs[["log_date", "readiness_score", "eye_strain", "sleep_hours"]].sort_values("log_date")
        chart_df = chart_df.set_index("log_date")
        st.line_chart(chart_df)
        st.caption("График по дням: Индекс готовности (0–100), Усталость глаз (1–10) и Часы сна.")
        
    with tab2:
        st.dataframe(df_logs, use_container_width=True)
else:
    st.write("В базе пока нет записей. Нажми кнопку расчета выше, чтобы добавить первый день.")
