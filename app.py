import time
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

from database import DatabaseManager
from engine import CoreEngine

try:
    from library_data import LIBRARY_CATALOG
except ImportError:
    LIBRARY_CATALOG = {}

# --- 1. НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(
    page_title="NeuroGuard SaaS",
    page_icon="⚡",
    layout="wide"
)

DatabaseManager.init_db()


# --- ДОПОЛНИТЕЛЬНЫЕ ТАБЛИЦЫ БД ДЛЯ НОВЫХ МОДУЛЕЙ ---
def init_extended_tables():
    conn = DatabaseManager.get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS energy_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            log_date TEXT,
            period TEXT,
            energy_lvl INTEGER,
            focus_lvl INTEGER,
            stress_lvl INTEGER,
            note TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS nutrition_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            log_date TEXT,
            calories INTEGER,
            protein INTEGER,
            fats INTEGER,
            carbs INTEGER,
            water_ml INTEGER,
            workout_done TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS book_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_title TEXT,
            category TEXT,
            status TEXT,
            insight TEXT,
            updated_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS custom_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quest_text TEXT
        )
    """)
    conn.commit()
    conn.close()


init_extended_tables()

# --- ЖЕЛЕЗОБЕТОННОЕ СОХРАНЕНИЕ СЕССИИ ПРИ ОБНОВЛЕНИИ (F5) ---
if "page" not in st.session_state:
    st.session_state.page = "landing"

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# Восстановление пользователя из URL-параметра при перезагрузке страницы
try:
    saved_uname = st.query_params.get("u", None)
    if st.session_state.current_user is None and saved_uname:
        conn = DatabaseManager.get_conn()
        c = conn.cursor()
        c.execute("SELECT id, username, is_pro FROM users WHERE username = ?", (saved_uname,))
        row = c.fetchone()
        conn.close()
        if row:
            st.session_state.current_user = {
                "id": row[0],
                "username": row[1],
                "is_pro": bool(row[2])
            }
            st.session_state.page = "dashboard"
except Exception:
    pass

if st.session_state.current_user is not None and st.session_state.page == "landing":
    st.session_state.page = "dashboard"

# --- 2. ПРЕМИАЛЬНЫЙ CSS-ВИЗУАЛ (TRUE GLASSMORPHISM BENTO) ---
bg_main = "#05070b"
border_col = "rgba(255, 255, 255, 0.1)"
text_col = "#f0f6fc"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background: radial-gradient(circle at 50% -10%, #111b2e 0%, {bg_main} 65%) !important;
        color: {text_col} !important;
        font-family: 'Inter', sans-serif !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: #080c14 !important;
        border-right: 1px solid {border_col} !important;
    }}
    h1, h2, h3, h4, p, span, label, .stMarkdown, [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
        color: {text_col} !important;
        font-family: 'Inter', sans-serif !important;
    }}
    code, pre, [data-testid="stMetricValue"] {{
        font-family: 'JetBrains Mono', monospace !important;
    }}
    div[data-baseweb="select"] > div, input, textarea {{
        background-color: #0f1728 !important;
        color: {text_col} !important;
        border: 1px solid rgba(88, 166, 255, 0.3) !important;
        border-radius: 12px !important;
    }}
    .hud-row {{
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }}
    .hud-pill {{
        background: rgba(15, 23, 40, 0.85);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 30px;
        padding: 6px 16px;
        font-size: 13px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }}
    .pro-pill {{
        border: 1px solid rgba(241,224,90,0.5) !important;
        background: linear-gradient(135deg, rgba(241,224,90,0.25), rgba(15,23,40,0.95)) !important;
        color: #f1e05a !important;
    }}
    .hyperfocus-pill {{
        border: 1px solid #ffd700 !important;
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.35), rgba(255, 140, 0, 0.2)) !important;
        color: #ffd700 !important;
        box-shadow: 0 0 25px rgba(255, 215, 0, 0.45) !important;
    }}
    .penalty-pill {{
        border: 1px solid #f85149 !important;
        background: linear-gradient(135deg, rgba(248, 81, 73, 0.3), rgba(15, 23, 40, 0.95)) !important;
        color: #f85149 !important;
        box-shadow: 0 0 20px rgba(248, 81, 73, 0.35) !important;
    }}
    .ach-card {{
        background: rgba(15, 23, 40, 0.75);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid {border_col};
        transition: all 0.3s ease;
    }}
    .ach-card:hover {{
        border-color: rgba(88, 166, 255, 0.5);
        transform: translateY(-2px);
    }}
    .ach-unlocked {{
        border: 1px solid rgba(63, 185, 80, 0.6) !important;
        background: linear-gradient(135deg, rgba(63,185,80,0.2), rgba(15,23,40,0.9)) !important;
        box-shadow: 0 0 25px rgba(63, 185, 80, 0.2);
    }}
    .ach-locked {{
        opacity: 0.35;
    }}
    .breath-box {{
        border-radius: 18px;
        padding: 24px;
        text-align: center;
        font-size: 22px;
        font-weight: 700;
        margin: 12px 0;
        border: 2px solid #58a6ff;
        background: rgba(88, 166, 255, 0.12);
        box-shadow: 0 0 35px rgba(88, 166, 255, 0.2);
        backdrop-filter: blur(12px);
    }}
    .tl-box {{
        border-radius: 14px;
        padding: 14px;
        background: rgba(15, 23, 40, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 10px;
    }}
    .book-card {{
        background: linear-gradient(180deg, rgba(16, 24, 42, 0.9) 0%, rgba(9, 14, 24, 0.95) 100%);
        border: 1px solid rgba(88, 166, 255, 0.2);
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 14px;
    }}
    /* СТИЛИ ПРЕМИАЛЬНОГО САЙТА */
    .saas-hero {{
        text-align: center;
        padding: 50px 20px 20px 20px;
    }}
    .system-footer {{
        text-align: center;
        font-size: 13px;
        color: #8b949e;
        margin-top: 60px;
        padding: 30px;
        border-top: 1px solid {border_col};
    }}
    </style>
""", unsafe_allow_html=True)


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (УРОВНИ, СТРИКИ, БАЗА КНИГ) ---
def get_cyber_title(lvl: int):
    if lvl >= 25:
        return "🌌 Абсолютный Монарх Сингулярности", "#ffd700"
    elif lvl >= 20:
        return "👑 Теневой Монарх S-Ранга", "#f1e05a"
    elif lvl >= 15:
        return "⚡ Кибер-Архитектор Матрицы", "#a371f7"
    elif lvl >= 10:
        return "🌟 Командор A-Ранга", "#3fb950"
    elif lvl >= 5:
        return "🛡️ Рыцарь B-Ранга", "#58a6ff"
    elif lvl >= 2:
        return "⚔️ Охотник C-Ранга", "#79c0ff"
    return "🌱 Неофит Системы", "#8b949e"


def calculate_traffic_light_streaks(df_rpg: pd.DataFrame):
    """
    Считает стрик (не прерывается, пока нет >3 пропущенных дней подряд),
    количество 🟢 зеленых, 🟡 желтых, 🔴 красных дней и % закрытия недели/месяца.
    """
    if df_rpg is None or df_rpg.empty or "log_date" not in df_rpg.columns:
        return {
            "streak": 0,
            "green": 0,
            "yellow": 0,
            "red": 0,
            "week_pct": 0,
            "month_pct": 0,
            "history": []
        }

    df_sorted = df_rpg.copy()
    df_sorted["parsed_date"] = pd.to_datetime(df_sorted["log_date"], errors="coerce").dt.date
    df_sorted = df_sorted.dropna(subset=["parsed_date"]).sort_values("parsed_date", ascending=False)
    date_map = {}
    for _, r in df_sorted.iterrows():
        d = r["parsed_date"]
        if d not in date_map:
            date_map[d] = int(r.get("plan_percent", 0))

    today_d = date.today()
    streak = 0
    consecutive_missed = 0
    check_d = today_d

    # Проверяем до 365 дней назад; стрик живет, пока пропущено <= 3 дней подряд
    for _ in range(365):
        if check_d in date_map:
            pct = date_map[check_d]
            if pct >= 50:
                streak += 1
                consecutive_missed = 0
            else:
                consecutive_missed += 1
        else:
            consecutive_missed += 1

        if consecutive_missed > 3:
            break
        check_d -= timedelta(days=1)

    green, yellow, red = 0, 0, 0
    history_records = []

    # Последние 30 дней для статистики месяца и светофора
    month_scores = []
    week_scores = []
    for i in range(30):
        d = today_d - timedelta(days=i)
        if d in date_map:
            p = date_map[d]
            if p >= 85:
                green += 1
                status = "🟢 Выполнено"
                col = "#3fb950"
            elif p >= 50:
                yellow += 1
                status = "🟡 Средне"
                col = "#d29922"
            else:
                red += 1
                status = "🔴 Слабо"
                col = "#f85149"
            month_scores.append(p)
            if i < 7:
                week_scores.append(p)
            history_records.append({"date": str(d), "pct": p, "status": status, "color": col})
        else:
            red += 1
            month_scores.append(0)
            if i < 7:
                week_scores.append(0)
            history_records.append({"date": str(d), "pct": 0, "status": "🔴 Пропуск", "color": "#f85149"})

    # Процент по реально заполненным дням или по календарной неделе/месяцу
    logged_week = [ date_map[today_d - timedelta(days=i)] for i in range(7) if (today_d - timedelta(days=i)) in date_map ]
    logged_month = [ date_map[today_d - timedelta(days=i)] for i in range(30) if (today_d - timedelta(days=i)) in date_map ]

    week_pct = int(round(sum(logged_week) / max(1, len(logged_week)))) if logged_week else 0
    month_pct = int(round(sum(logged_month) / max(1, len(logged_month)))) if logged_month else 0

    return {
        "streak": streak,
        "green": green,
        "yellow": yellow,
        "red": red,
        "week_pct": week_pct,
        "month_pct": month_pct,
        "history": history_records
    }


DEFAULT_EXTENDED_LIBRARY = {
    "🧠 Психология & Менталка": [
        {"title": "Думай медленно... решай быстро", "author": "Даниэль Канеман", "status": "Прочитано", "desc": "Фундаментальный труд о когнитивных искажениях и двух системах мышления."},
        {"title": "Атомные привычки", "author": "Джеймс Клир", "status": "Прочитано", "desc": "Система формирования полезных привычек и дисциплины через микро-шаги."},
        {"title": "Поток: Психология оптимального переживания", "author": "Михай Чиксентмихайи", "status": "Прочитано", "desc": "Как входить в состояние гиперфокуса и получать максимум от сложной работы."},
        {"title": "Эмоциональный интеллект", "author": "Дэниел Гоулман", "status": "В процессе", "desc": "Контроль эмоций, стрессоустойчивость и лидерство."},
        {"title": "Психология влияния", "author": "Роберт Чалдини", "status": "В планах", "desc": "Механизмы убеждения, переговоров и защиты от манипуляций."},
        {"title": "Не навреди. Истории о жизни, смерти и нейрохирургии", "author": "Генри Марш", "status": "В планах", "desc": "Взгляд на работу мозга, принятие решений под давлением и ответственность."},
        {"title": "Человек в поисках смысла", "author": "Виктор Франкл", "status": "Прочитано", "desc": "Психология несгибаемой воли и преодоления экстремальных испытаний."},
        {"title": "Гибкое сознание", "author": "Кэрол Дуэк", "status": "В планах", "desc": "Установка на рост против фиксированного мышления в спорте и науке."}
    ],
    "🧬 Биохакинг & Сон": [
        {"title": "Зачем мы спим", "author": "Мэттью Уокер", "status": "Прочитано", "desc": "Наука о сне: как фазы сна перезагружают ЦНС, память и мышечный рост."},
        {"title": "Биохакинг мозга", "author": "Дэйв Эспри", "status": "В процессе", "desc": "Практическое руководство по разгону митохондрий, нейрогенезу и фокусу."},
        {"title": "Зажги себя! Жизнь в движении", "author": "Джон Рейти", "status": "Прочитано", "desc": "Как физические нагрузки и спорт напрямую выращивают новые нейроны."},
        {"title": "Кишечник и мозг", "author": "Дэвид Перлмуттер", "status": "В планах", "desc": "Влияние питания и микробиома на скорость мышления и защиту от воспалений."},
        {"title": "Кислородное преимущество", "author": "Патрик Маккеон", "status": "В процессе", "desc": "Дыхательные протоколы для повышения выносливости и снижения пульса."},
        {"title": "Циркадный код", "author": "Сатчин Панда", "status": "В планах", "desc": "Как синхронизировать биоритмы, свет, питание и тренировки для максимума энергии."},
        {"title": "Дофаминовое поколение", "author": "Анна Лембке", "status": "Прочитано", "desc": "Как перезагрузить систему вознаграждения мозга и избавиться от дешевого дофамина."}
    ],
    "💻 Продуктивность & Кодинг": [
        {"title": "Чистый код (Clean Code)", "author": "Роберт Мартин", "status": "В процессе", "desc": "Стандарты индустрии по созданию масштабируемой и чистой архитектуры."},
        {"title": "Грокаем алгоритмы", "author": "Адитья Бхаргава", "status": "Прочитано", "desc": "Наглядный фундамент по графам, динамическому программированию и структурам данных."},
        {"title": "Алгоритмы. Построение и анализ", "author": "Томас Кормен", "status": "В процессе", "desc": "Библия олимпиадного программирования и компьютерных наук."},
        {"title": "В работу с головой (Deep Work)", "author": "Кэл Ньюпорт", "status": "Прочитано", "desc": "Методика экстремальной концентрации без отвлечений в цифровую эпоху."},
        {"title": "Совершенный код", "author": "Стив Макконнелл", "status": "В планах", "desc": "Полная энциклопедия проектирования профессиональных программных систем."},
        {"title": "Python. К вершинам мастерства (Fluent Python)", "author": "Лучано Рамальо", "status": "В процессе", "desc": "Глубокое погружение в устройство языка Python для продвинутых разработчиков."},
        {"title": "От нуля к единице (Zero to One)", "author": "Питер Тиль", "status": "Прочитано", "desc": "Как создавать технологические стартапы и монополии будущего."}
    ],
    "🥋 Философия Воина & Экстрим": [
        {"title": "Книга Пяти Колец", "author": "Миямото Мусаси", "status": "Прочитано", "desc": "Легендарный трактат непобежденного мастера меча о стратегии, духе и тайминге."},
        {"title": "Ничто не может меня сломить (Can't Hurt Me)", "author": "Дэвид Гоггинс", "status": "Прочитано", "desc": "Правило 40%, выход за пределы боли и ультрамарафонская ментальная броня."},
        {"title": "В разреженном воздухе", "author": "Джон Кракауэр", "status": "В процессе", "desc": "Хроника штурма Эвереста на высоте более 8000 метров в зоне смерти."},
        {"title": "Искусство войны", "author": "Сунь-Цзы", "status": "Прочитано", "desc": "Древняя военная стратегия, применимая в поединках, бизнесе и олимпиадах."},
        {"title": "Бусидо. Кодекс самурая", "author": "Инадзо Нитобэ", "status": "В планах", "desc": "Дисциплина, честь и хладнокровие восточных боевых искусств."},
        {"title": "Тренировочная зона (Convict Conditioning)", "author": "Пол Уэйд", "status": "Прочитано", "desc": "Прогрессии калистеники и работы с собственным весом до сверхчеловеческой силы."}
    ]
}


# =====================================================================
# ЭКРАН 1: 🌟 ПРЕМИАЛЬНЫЙ СААС-ЛЕНДИНГ
# =====================================================================
if st.session_state.page == "landing":
    st.markdown("""
        <div class="saas-hero">
            <span class="hud-pill pro-pill" style="margin-bottom: 20px;">⚡ Next-Gen Product & Biohack Ecosystem</span>
            <h1 style="font-size: 50px; font-weight: 900; letter-spacing: -1.5px; margin-bottom: 15px; background: linear-gradient(135deg, #ffffff 20%, #58a6ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">NEUROGUARD</h1>
            <p style="font-size: 18px; color: #8b949e; max-width: 600px; margin: 0 auto 30px auto; line-height: 1.5;">Архитектура продуктивности нового поколения. Контроль ЦНС, RPG-геймификация и предиктивное восстановление.</p>
        </div>
    """, unsafe_allow_html=True)

    try:
        st.image("hero.jpg", use_container_width=True)
    except Exception:
        pass

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2, c_btn3 = st.columns([1, 1.3, 1])
    with c_btn2:
        if st.button("🚀 ЗАПУСТИТЬ СИСТЕМУ", use_container_width=True, type="primary"):
            st.session_state.page = "auth"
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; margin-bottom: 30px; font-weight: 800; letter-spacing: 1px;'>🛠️ КЛЮЧЕВЫЕ МОДУЛИ ПЛАТФОРМЫ</h3>", unsafe_allow_html=True)

    # Функция для рендеринга премиальной карточки (картинка + текст поверх или внутри)
    def render_bento_module(emoji, title, desc, img_file):
        st.markdown(f"""
            <div style="
                background: linear-gradient(180deg, rgba(13,20,35,0.9) 0%, rgba(7,11,19,0.95) 100%);
                border: 1px solid rgba(88, 166, 255, 0.22);
                border-radius: 24px;
                padding: 24px;
                margin-bottom: 25px;
                box-shadow: 0 15px 40px rgba(0,0,0,0.5);
                position: relative;
            ">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 28px; background: rgba(88,166,255,0.15); padding: 8px 12px; border-radius: 14px;">{emoji}</span>
                    <h3 style="margin: 0; font-size: 20px; font-weight: 800;">{title}</h3>
                </div>
                <p style="color: #8b949e; font-size: 14px; line-height: 1.6; margin-bottom: 16px;">{desc}</p>
            </div>
        """, unsafe_allow_html=True)
        try:
            st.image(img_file, use_container_width=True)
        except Exception:
            pass
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    bc1, bc2 = st.columns(2)

    with bc1:
        render_bento_module(
            "🛡️", "Био-Мониторинг ЦНС & AI-Предиктор",
            "Интеллектуальный трекинг сна, экранного времени, энергии и спазма глаз. Предиктивный движок включает Красный протокол при риске выгорания.",
            "bio.jpg"
        )
        render_bento_module(
            "🏆", "Зал Славы (100 Трофеев)",
            "Элитная система достижений за успехи в учебе, кодинге, олимпиадах, жиме 100+ кг, восхождениях и боевых искусствах.",
            "trophies.jpg"
        )

    with bc2:
        render_bento_module(
            "⚔️", "RPG-Прокачка, Гиперфокус & Светофор",
            "Геймификация рутины: уровни, кибер-титулы, режим Гиперфокуса (+50% XP), светофорные стрики без жесткого сброса и тепловая карта.",
            "rpg.jpg"
        )
        render_bento_module(
            "🧘", "Нейро-Резет, Тренировки & База Знаний",
            "Интерактивные таймеры пауз, Табата-секундомер, трекер КБЖУ, умный советник и встроенная библиотека топ-литературы.",
            "reset.jpg"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn4, c_btn5, c_btn6 = st.columns([1, 1.3, 1])
    with c_btn5:
        if st.button("⚡ ВОЙТИ В АККАУНТ", use_container_width=True, type="primary"):
            st.session_state.page = "auth"
            st.rerun()

    st.markdown("""
        <div class="system-footer">
            🟢 System Online • Secured with SQLite & Streamlit Core<br>
            © 2026 NeuroGuard Inc. Все права защищены.
        </div>
    """, unsafe_allow_html=True)


# =====================================================================
# ЭКРАН 2: 🔐 ОКНО ВХОДА И РЕГИСТРАЦИИ (Auth Gate)
# =====================================================================
elif st.session_state.page == "auth":
    st.markdown("<h2 style='text-align: center; margin-top: 40px;'>🔐 Авторизация в системе</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e; margin-bottom: 30px;'>Введите учетные данные для доступа к защищенному дашборду</p>", unsafe_allow_html=True)
    
    col_a1, col_a2, col_a3 = st.columns([1, 1.2, 1])
    with col_a2:
        auth_mode = st.radio("Режим:", ["Вход в аккаунт", "Создать профиль"], horizontal=True)
        inp_user = st.text_input("Никнейм", placeholder="Например: Igor_Founder")
        inp_pin = st.text_input("PIN-код", type="password", max_chars=8, placeholder="••••")

        st.markdown("<br>", unsafe_allow_html=True)
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("⬅️ Назад", use_container_width=True):
                st.session_state.page = "landing"
                st.rerun()
        with col_act2:
            if st.button("🚀 Продолжить", use_container_width=True, type="primary"):
                is_reg = (auth_mode == "Создать профиль")
                user_obj, err = DatabaseManager.authenticate_or_register(
                    inp_user, inp_pin, create_new=is_reg
                )
                if err:
                    st.error(err)
                else:
                    st.session_state.current_user = user_obj
                    st.session_state.page = "dashboard"
                    try:
                        st.query_params["u"] = user_obj["username"]
                    except Exception:
                        pass
                    st.success(f"Добро пожаловать, {user_obj['username']}!")
                    st.rerun()


# =====================================================================
# ЭКРАН 3: ⚡ ОСНОВНАЯ РАБОЧАЯ СРЕДА (Dashboard / HUD)
# =====================================================================
elif st.session_state.page == "dashboard":
    cur_u = st.session_state.current_user
    if not cur_u:
        st.session_state.page = "auth"
        st.rerun()

    uid = cur_u["id"]
    uname = cur_u["username"]
    is_pro = cur_u["is_pro"]

    df_logs = DatabaseManager.load_health_logs(uid)
    df_rpg = DatabaseManager.load_rpg_logs(uid)

    # Расчет опыта, уровня, титула и режима Гиперфокуса / Штрафа
    hist_xp = int(df_rpg["xp_earned"].sum()) if (df_rpg is not None and not df_rpg.empty and "xp_earned" in df_rpg.columns) else 0
    player_lvl = (hist_xp // 500) + 1
    xp_in_current_lvl = hist_xp % 500
    lvl_progress_pct = xp_in_current_lvl / 500.0
    cyber_title, title_col = get_cyber_title(player_lvl)

    last_readiness = int(df_logs.iloc[0]["readiness_score"]) if (df_logs is not None and not df_logs.empty and "readiness_score" in df_logs.columns) else 75
    last_plan_pct = int(df_rpg.iloc[0]["plan_percent"]) if (df_rpg is not None and not df_rpg.empty and "plan_percent" in df_rpg.columns) else 80

    # Проверка Гиперфокуса (+50% XP) или Истощения (-50 XP)
    is_hyperfocus = (last_plan_pct >= 95 and last_readiness >= 75)
    is_exhausted = (last_plan_pct < 50 and last_readiness < 50)

    streak_data = calculate_traffic_light_streaks(df_rpg)

    # САЙДБАР
    with st.sidebar:
        st.header("🔐 Аккаунт")
        pro_badge = "💎 PRO" if cur_u["is_pro"] else "🆓 FREE"
        st.markdown(f"Профиль: **{cur_u['username']}** ({pro_badge})")
        st.markdown(f"Титул: <b style='color:{title_col};'>{cyber_title}</b>", unsafe_allow_html=True)
        st.progress(lvl_progress_pct, text=f"LVL {player_lvl} ({xp_in_current_lvl}/500 XP до LVL {player_lvl + 1})")

        if st.button("🚪 Выйти из аккаунта", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.page = "landing"
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.rerun()

        st.divider()
        st.header("🔥 Светофор Стриков")
        st.markdown(f"**Активная серия:** `{streak_data['streak']} дн.` *(живет до 3 пропусков)*")
        st.markdown(f"🟢 Отлично: **{streak_data['green']}** | 🟡 Средне: **{streak_data['yellow']}** | 🔴 Пропуск: **{streak_data['red']}**")
        st.markdown(f"📊 Закрытие недели: **{streak_data['week_pct']}%**")
        st.markdown(f"📅 Закрытие месяца: **{streak_data['month_pct']}%**")

        st.divider()
        st.header("💎 NeuroGuard PRO")
        is_pro_toggle = st.toggle(
            "Активировать PRO-режим",
            value=cur_u["is_pro"],
            help="Дает +25% буст к XP и экспорт отчетов."
        )
        if is_pro_toggle != cur_u["is_pro"]:
            DatabaseManager.set_pro_status(cur_u["id"], is_pro_toggle)
            st.session_state.current_user["is_pro"] = is_pro_toggle
            st.rerun()

        st.divider()
        dark_mode = st.toggle("🌙 Eye-Safe Mode (Тёмная тема)", value=True)

    # ВЕРХНИЙ HUD-БАР
    rank_txt, rank_col = CoreEngine.get_rank_badge(last_readiness)
    tier_pill = '<span class="hud-pill pro-pill">💎 PRO x1.25 XP</span>' if is_pro else '<span class="hud-pill">🆓 FREE</span>'

    if is_hyperfocus:
        mode_pill = '<span class="hud-pill hyperfocus-pill">🔥 ГИПЕРФОКУС (+50% XP)</span>'
    elif is_exhausted:
        mode_pill = '<span class="hud-pill penalty-pill">⚠️ ИСТОЩЕНИЕ (-50 XP)</span>'
    else:
        mode_pill = '<span class="hud-pill">⚡ ШТАТНЫЙ РЕЖИМ</span>'

    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; margin-bottom:12px;">
        <div>
            <h3 style="margin:0; font-weight:800;">⚡ {uname} <span style="font-size:15px; color:{title_col}; font-weight:600;">• {cyber_title}</span></h3>
        </div>
        <div class="hud-row" style="margin:0;">
            {mode_pill}
            {tier_pill}
            <span class="hud-pill" style="border-color:{rank_col}; color:{rank_col};">{rank_txt}</span>
            <span class="hud-pill">🔥 Стрик: {streak_data['streak']} дн.</span>
            <span class="hud-pill">🏅 LVL {player_lvl}</span>
            <span class="hud-pill">✨ {hist_xp} XP</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_bio, tab_rpg, tab_train, tab_books, tab_goals, tab_ach, tab_sos, tab_rep = st.tabs([
        "🛡️ БИО & ЭНЕРГИЯ",
        "⚔️ СТАТЫ & СТРИКИ",
        "🏋️ ТРЕНИРОВКИ & ПИТАНИЕ",
        "📚 ЛИТЕРАТУРА",
        "🎯 ЦЕЛИ",
        "🏆 100 ТРОФЕЕВ",
        "🧘 РЕЗЕТ",
        "📄 ОТЧЕТ & ТОП"
    ])

    # =================================================================
    # ВКЛАДКА 1: 🛡️ БИО, AI-ПРЕДИКТОР & ДНЕВНИК ЭНЕРГИИ
    # =================================================================
    with tab_bio:
        col_input, col_result = st.columns([1.1, 1])
        with col_input:
            st.markdown("#### 🎛️ Параметры био-системы")
            log_date = st.date_input("📅 Дата", value=date.today(), key="health_date")

            c1, c2 = st.columns(2)
            with c1:
                sleep_hours = st.slider("💤 Сон (ч)", 0.0, 12.0, 7.5, 0.5)
                study_hours = st.slider("💻 Экран / Бота (ч)", 0.0, 14.0, 5.0, 0.5)
                training_type = st.selectbox(
                    "🥋 Режим нагрузки",
                    ["Отдых", "ОФП / Турники / Бег", "Техника / Кобудо (без контакта)", "Спарринги / Контакт"]
                )
            with c2:
                sleep_quality = st.slider("🔋 Качество сна", 1, 10, 8)
                eye_strain = st.slider("👁️ Спазм глаз", 1, 10, 3)
                is_rest = (training_type == "Отдых")
                training_intensity = st.slider(
                    "🔥 Тяжесть спорта", 0, 10,
                    value=0 if is_rest else 5,
                    disabled=is_rest
                )

            head_impact = st.checkbox("⚠️ Ударная нагрузка / резкое натуживание")
            analyze_btn = st.button("⚡ Сохранить био-статус", use_container_width=True, type="primary")

        with col_result:
            st.markdown("#### 📡 Индекс готовности & Выгорание")
            current_score = CoreEngine.calculate_readiness(
                sleep_hours, sleep_quality, study_hours, eye_strain, training_intensity, head_impact
            )

            b_rank, b_col = CoreEngine.get_rank_badge(current_score)
            st.markdown(f'<span class="hud-pill" style="border-color:{b_col};">{b_rank}</span>', unsafe_allow_html=True)
            st.metric(label="🔋 Заряд организма (Readiness)", value=f"{current_score}%")
            st.progress(current_score / 100)

            burnout = CoreEngine.analyze_burnout_risk(df_logs, df_rpg)
            st.markdown(f"""
            <div style="background-color:{burnout['color']}18; border:1px solid {burnout['color']}; border-radius:12px; padding:14px; margin-top:12px;">
                <b style="color:{burnout['color']};">{burnout['risk_level']}</b><br>
                <p style="margin:6px 0 0 0; font-size:13px; color:#c9d1d9;">{burnout['message']}</p>
            </div>
            """, unsafe_allow_html=True)

            # AI-Предиктор 7-дневного тренда ЦНС
            st.markdown("##### 🤖 AI-Предиктор тренда ЦНС (7 дней)")
            if df_logs is not None and not df_logs.empty and len(df_logs) >= 2:
                h7 = df_logs.head(7)
                avg_slp = h7["sleep_hours"].mean()
                avg_scr = h7["study_hours"].mean()
                low_slp_days = int((h7["sleep_hours"] < 6.5).sum())
                if low_slp_days >= 3 or (avg_slp < 6.5 and avg_scr > 7.5):
                    st.error(
                        f"🚨 **КРАСНЫЙ ПРОТОКОЛ ЦНС АКТИВИРОВАН:** За последние дни зафиксировано {low_slp_days} дн. недосыпа "
                        f"(средний сон {avg_slp:.1f}ч при экране {avg_scr:.1f}ч). Запрещены тяжелые проходки в жиме и контактные спарринги! "
                        f"Приоритет: сон 8.5+ часов и пальминг."
                    )
                else:
                    st.success(
                        f"🧠 **Прогноз ИИ благоприятный:** Средний сон за неделю {avg_slp:.1f}ч, экран {avg_scr:.1f}ч. "
                        f"Нервная система готова к пиковым когнитивным и силовым нагрузкам."
                    )
            else:
                st.caption("Накопите минимум 2 записи в био-базе для запуска 7-дневного AI-прогноза.")

            if analyze_btn:
                DatabaseManager.save_health_log((
                    uid, str(log_date), sleep_hours, sleep_quality, study_hours,
                    eye_strain, training_type, training_intensity,
                    int(head_impact), current_score, burnout['message']
                ))
                st.success("✅ Био-статус сохранен!")
                st.rerun()

        st.divider()
        # --- ДНЕВНИК ЭНЕРГИИ И ФОКУСА (УТРО / ДЕНЬ / ВЕЧЕР) ---
        st.markdown("#### ⚡ Дневник Энергии и Ментального Фокуса (Пики продуктивности)")
        en_c1, en_c2 = st.columns([1, 1.2])
        with en_c1:
            en_period = st.radio("Период суток:", ["🌅 Утро", "☀️ День", "🌙 Вечер"], horizontal=True)
            en_val = st.slider("🔋 Уровень физической энергии (1-10)", 1, 10, 8, key="en_slider")
            foc_val = st.slider("🎯 Концентрация и ясность ума (1-10)", 1, 10, 8, key="foc_slider")
            str_val = st.slider("🌋 Уровень стресса / напряжения (1-10)", 1, 10, 3, key="str_slider")
            en_note = st.text_input("Короткая заметка по состоянию:", placeholder="После тренировки и холодного душа фокус 10/10")

            if st.button("💾 Зафиксировать импульс энергии", use_container_width=True):
                conn = DatabaseManager.get_conn()
                c = conn.cursor()
                c.execute(
                    "INSERT INTO energy_logs (user_id, log_date, period, energy_lvl, focus_lvl, stress_lvl, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (uid, str(date.today()), en_period, en_val, foc_val, str_val, en_note.strip())
                )
                conn.commit()
                conn.close()
                st.success("✅ Запись энергии добавлена!")
                st.rerun()

        with en_c2:
            conn = DatabaseManager.get_conn()
            df_en = pd.read_sql_query(
                "SELECT log_date, period, energy_lvl, focus_lvl, stress_lvl, note FROM energy_logs WHERE user_id = ? ORDER BY id DESC LIMIT 15",
                conn, params=(uid,)
            )
            conn.close()
            if not df_en.empty:
                st.markdown("##### 📈 График твоих биоритмов (Энергия vs Фокус vs Стресс)")
                chart_en = df_en[["energy_lvl", "focus_lvl", "stress_lvl"]].iloc[::-1].reset_index(drop=True)
                st.line_chart(chart_en)
                st.dataframe(df_en.head(5), use_container_width=True, hide_index=True)
            else:
                st.info("Запиши свой первый замер энергии (Утро / День / Вечер), чтобы увидеть кривую продуктивности!")

    # =================================================================
    # ВКЛАДКА 2: ⚔️ СТАТЫ, КОНСТРУКТОР КВЕСТОВ & СВЕТОФОРНЫЕ СТРИКИ
    # =================================================================
    with tab_rpg:
        rpg_col1, rpg_col2 = st.columns([1.1, 1])
        with rpg_col1:
            st.markdown("#### 🎯 Квесты на день")
            rpg_date = st.date_input("📅 Дата", value=date.today(), key="rpg_date")

            # Загрузка кастомных привычек пользователя из БД
            conn = DatabaseManager.get_conn()
            custom_q_df = pd.read_sql_query("SELECT id, quest_text FROM custom_quests WHERE user_id = ?", conn, params=(uid,))
            conn.close()

            with st.expander("➕ Конструктор квестов (добавить свою привычку)"):
                new_q_txt = st.text_input("Новая ежедневная привычка:", placeholder="Например: Выпить 2.5л воды / 30 мин английского")
                if st.button("Добавить в список квестов", use_container_width=True):
                    if new_q_txt.strip():
                        conn = DatabaseManager.get_conn()
                        c = conn.cursor()
                        c.execute("INSERT INTO custom_quests (user_id, quest_text) VALUES (?, ?)", (uid, new_q_txt.strip()))
                        conn.commit()
                        conn.close()
                        st.success("Привычка добавлена в шаблон!")
                        st.rerun()

            base_quests = [
                "100 подтягиваний",
                "5 задач (ЕГЭ / Python)",
                "20 страниц книги",
                "5 раундов техники / кобудо"
            ]
            if not custom_q_df.empty:
                base_quests.extend(custom_q_df["quest_text"].tolist())

            default_plan = "\n".join(base_quests)
            plan_text = st.text_area("Список задач:", value=default_plan, height=110)

            tasks_list = [t.strip() for t in plan_text.split("\n") if t.strip()]
            completed_tasks = 0
            if tasks_list:
                for idx, task_item in enumerate(tasks_list):
                    if st.checkbox(f"✅ {task_item}", key=f"task_chk_{idx}"):
                        completed_tasks += 1
                plan_percent = int(round((completed_tasks / len(tasks_list)) * 100))
            else:
                plan_percent = 70

            rc1, rc2 = st.columns(2)
            with rc1:
                exercises_reps = st.number_input("💪 Повторения (ОФП)", 0, 2000, 100, 10)
                agility_drills = st.number_input("⚡ Раунды техники", 0, 50, 5, 1)
                book_pages = st.number_input("📖 Страницы книг", 0, 500, 20, 5)
            with rc2:
                topics_learned = st.number_input("🧠 Пройдено тем", 0, 20, 1, 1)
                tasks_solved = st.number_input("💻 Решено задач", 0, 200, 5, 1)

            daily_note = st.text_input("📓 Заметка воина:", placeholder="Сделал сотку на турнике")
            save_rpg_btn = st.button("⚔️ Зафиксировать статы", use_container_width=True, type="primary")

        with rpg_col2:
            st.markdown("#### 🧬 Характеристики Персонажа & Бонусы Режима")
            str_pts, agi_pts, int_pts, dsc_pts, total_actions, xp_earned = CoreEngine.calculate_rpg_stats(
                exercises_reps, agility_drills, book_pages, topics_learned, tasks_solved, plan_percent, is_pro=is_pro
            )

            # Модификатор Гиперфокуса (+50% XP) или Штрафа при провале (<50% плана)
            mode_status_str = "Активен"
            if plan_percent == 100:
                xp_earned = int(round(xp_earned * 1.5))
                mode_status_str = "🔥 ГИПЕРФОКУС (+50% XP)"
                st.success("🔥 **АКТИВИРОВАН ГИПЕРФОКУС!** Все квесты закрыты на 100% — начисляется **+50% бонусного XP**!")
            elif plan_percent < 50:
                xp_earned = max(0, xp_earned - 50)
                mode_status_str = "⚠️ ШТРАФ (-50 XP)"
                st.warning("⚠️ **Штраф дисциплины:** Выполнено менее 50% плана (-50 XP). Но твой стрик сохраняется (до 3 пропусков подряд)!")

            st.markdown(f"""
            <div class="hud-row">
                <span class="hud-pill">🎯 План: {plan_percent}%</span>
                <span class="hud-pill">✨ +{xp_earned} XP</span>
                <span class="hud-pill">💪 STR +{str_pts}</span>
                <span class="hud-pill">⚡ AGI +{agi_pts}</span>
                <span class="hud-pill">🧠 INT +{int_pts}</span>
                <span class="hud-pill">👑 DSC +{dsc_pts}</span>
            </div>
            """, unsafe_allow_html=True)

            # Сводка по закрытию недели и месяца
            st.markdown("##### 📊 Светофорная Статистика (за 30 дней)")
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("🟢 Выполнено", f"{streak_data['green']} дн.")
            sc2.metric("🟡 Частично", f"{streak_data['yellow']} дн.")
            sc3.metric("🔴 Пропущено", f"{streak_data['red']} дн.")

            st.progress(streak_data["week_pct"] / 100.0, text=f"📅 Процент закрытия текущей недели: {streak_data['week_pct']}%")
            st.progress(streak_data["month_pct"] / 100.0, text=f"🗓️ Процент закрытия текущего месяца: {streak_data['month_pct']}%")

            if save_rpg_btn:
                DatabaseManager.save_rpg_log((
                    uid, str(rpg_date), exercises_reps, agility_drills, book_pages,
                    topics_learned, tasks_solved, plan_text, plan_percent,
                    total_actions, xp_earned, str_pts, agi_pts, int_pts, dsc_pts, mode_status_str, daily_note
                ))
                st.success("✅ Статы сохранены в БД!")
                st.rerun()

        st.divider()
        st.markdown("#### 🚦 Светофорная лента последних 14 дней (Стрик не сгорает до 3 пропусков)")
        if streak_data["history"]:
            pills_html = '<div class="hud-row">'
            for item in streak_data["history"][:14]:
                pills_html += f'<span class="hud-pill" style="border-color:{item["color"]}; color:{item["color"]};">{item["date"][5:]}: {item["status"]} ({item["pct"]}%)</span>'
            pills_html += '</div>'
            st.markdown(pills_html, unsafe_allow_html=True)

        st.markdown("#### 🔥 Тепловая карта активности (GitHub-Style Heatmap)")
        if df_rpg is not None and not df_rpg.empty and "log_date" in df_rpg.columns and "plan_percent" in df_rpg.columns:
            heat_df = df_rpg[["log_date", "plan_percent"]].sort_values("log_date")
            st.bar_chart(heat_df.set_index("log_date"), color="#3fb950")
        else:
            st.info("Сохрани первый RPG-лог выше, чтобы активировать тепловую карту!")

    # =================================================================
    # ВКЛАДКА 3: 🏋️ ТРЕНИРОВКИ, СЕКУНДОМЕРЫ & ТРЕКЕР ПИТАНИЯ
    # =================================================================
    with tab_train:
        st.markdown("#### 🏋️ Тренировочный Полигон: Программы, Табата и Трекер Питания")
        tr_col1, tr_col2 = st.columns([1.1, 1])

        with tr_col1:
            st.markdown("##### 📋 Боевые и Силовые Протоколы")
            workout_choice = st.selectbox(
                "Выбери тренировочный комплекс:",
                [
                    "🔥 Калистеника: 'Сотка за 14 минут' + Горизонт",
                    "🥋 Боевые Искусства: Каратэ / Кобудо / Самбо",
                    "🦾 Силовой Экстрим: Штурм Жима 100+ кг и База",
                    "🏔️ Альпинизм & Выносливость: Подготовка к Вершинам"
                ]
            )

            if "Калистеника" in workout_choice:
                st.info(
                    "**Протокол Воркаута:**\n"
                    "1. **Разминка суставов и плечевого пояса:** 7 мин.\n"
                    "2. **Закрытый горизонт / Планш на паралетсах:** 5 подходов по 10–15 сек удержания.\n"
                    "3. **Челлендж '100 подтягиваний':** EMOM (каждую минуту по 7–8 чистых подтягиваний) до 100 повторений.\n"
                    "4. **Брусья с весом / Отжимания в стойке:** 4 подхода по 12–15 раз.\n"
                    "5. **Заминка:** Вис на перекладине 90 сек для декомпрессии позвоночника."
                )
            elif "Боевые" in workout_choice:
                st.info(
                    "**Протокол Додзё (Каратэ / Кобудо / Самбо):**\n"
                    "1. **Суставная разминка и растяжка шпагатов:** 10 мин.\n"
                    "2. **Кихон и взрывные связки руками/ногами:** 5 раундов по 3 мин.\n"
                    "3. **Кобудо (работа с шестом бо / нунчаку / сай):** 5 раундов на филигранный контроль и скорость.\n"
                    "4. **Борцовская резина / проходы и броски (Самбо):** 4 серии по 20 скоростных тяг.\n"
                    "5. **Дыхание Санчин / Концентрация:** 5 мин."
                )
            elif "Силовой" in workout_choice:
                st.info(
                    "**Протокол Железного Цеха:**\n"
                    "1. **Жим штанги лежа (пирамида к 100+ кг):** Разминка 50кг×12, 70кг×8, 85кг×5, Рабочие 95–105кг 3×3.\n"
                    "2. **Подтягивания с дополнительным весом (+15–25 кг):** 4×6.\n"
                    "3. **Приседания со штангой / Становая тяга:** 4×6 с идеальной техникой спины.\n"
                    "4. **Укрепление хвата и предплечий:** Удержание блинов щипковым хватом 3×45 сек."
                )
            else:
                st.info(
                    "**Протокол Высотной Выносливости (Эверест / Бег):**\n"
                    "1. **Кросс в темпе пульсовой зоны 2 (135–150 уд/мин):** 5–10 км.\n"
                    "2. **Зашагивания на высокую тумбу с рюкзаком:** 4 серии по 50 шагов.\n"
                    "3. **Статика ног ('Стульчик' у стены):** 3 подхода по 2 минуты."
                )

            st.markdown("##### ⏱️ Интерактивные Таймеры Тренировки")
            tm_c1, tm_c2, tm_c3 = st.columns(3)
            timer_display = st.empty()
            timer_bar = st.progress(0)

            with tm_c1:
                if st.button("🔥 Табата (20с/10с)", use_container_width=True, type="primary"):
                    for s in range(20, 0, -1):
                        timer_display.markdown(f'<div class="breath-box" style="border-color:#f85149;">🔥 РАБОТА НА МАКСИМУМ: <b>{s} сек</b></div>', unsafe_allow_html=True)
                        timer_bar.progress((20 - s) / 20.0)
                        time.sleep(1)
                    for s in range(10, 0, -1):
                        timer_display.markdown(f'<div class="breath-box" style="border-color:#3fb950;">🌿 ОТДЫХ И ДЫХАНИЕ: <b>{s} сек</b></div>', unsafe_allow_html=True)
                        timer_bar.progress((10 - s) / 10.0)
                        time.sleep(1)
                    timer_display.markdown('<div class="breath-box" style="border-color:#3fb950;">✅ Цикл Табаты выполнен!</div>', unsafe_allow_html=True)

            with tm_c2:
                if st.button("🥊 Раунд (60 сек)", use_container_width=True):
                    for s in range(60, 0, -1):
                        timer_display.markdown(f'<div class="breath-box" style="border-color:#d29922;">🥋 БОЕВОЙ РАУНД: <b>{s} сек</b></div>', unsafe_allow_html=True)
                        timer_bar.progress((60 - s) / 60.0)
                        time.sleep(1)
                    timer_display.markdown('<div class="breath-box" style="border-color:#3fb950;">🔔 ГОНГ! Раунд окончен.</div>', unsafe_allow_html=True)

            with tm_c3:
                if st.button("❄️ Отдых (45 сек)", use_container_width=True):
                    for s in range(45, 0, -1):
                        timer_display.markdown(f'<div class="breath-box" style="border-color:#58a6ff;">💧 ВОССТАНОВЛЕНИЕ МЕЖДУ ПОДХОДАМИ: <b>{s} сек</b></div>', unsafe_allow_html=True)
                        timer_bar.progress((45 - s) / 45.0)
                        time.sleep(1)
                    timer_display.markdown('<div class="breath-box" style="border-color:#3fb950;">⚡ Время вышло! Заход на подход!</div>', unsafe_allow_html=True)

        with tr_col2:
            st.markdown("##### 🥩 Трекер Питания, КБЖУ и Водного Баланса")
            nut_date = st.date_input("Дата рациона:", value=date.today(), key="nut_date")
            nc1, nc2 = st.columns(2)
            with nc1:
                cal_in = st.number_input("🔥 Калории (ккал)", 0, 6000, 2600, 100)
                prot_in = st.number_input("🥩 Белки (г)", 0, 400, 150, 5)
            with nc2:
                fats_in = st.number_input("🥑 Жиры (г)", 0, 300, 80, 5)
                carbs_in = st.number_input("🍚 Углеводы (г)", 0, 800, 300, 10)

            water_in = st.slider("💧 Выпито чистой воды (мл)", 0, 4500, 2200, 250)
            st.progress(min(1.0, water_in / 2500.0), text=f"Водный баланс: {water_in} / 2500 мл ({int(round(water_in / 25)) }%)")

            if st.button("💾 Сохранить дневной рацион и тренировку", use_container_width=True, type="primary"):
                conn = DatabaseManager.get_conn()
                c = conn.cursor()
                c.execute(
                    "INSERT INTO nutrition_logs (user_id, log_date, calories, protein, fats, carbs, water_ml, workout_done) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (uid, str(nut_date), cal_in, prot_in, fats_in, carbs_in, water_in, workout_choice)
                )
                conn.commit()
                conn.close()
                st.success("✅ Данные по КБЖУ, воде и тренировке сохранены!")
                st.rerun()

            conn = DatabaseManager.get_conn()
            df_nut = pd.read_sql_query(
                "SELECT log_date as 'Дата', calories as 'Ккал', protein as 'Белки(г)', carbs as 'Углеводы(г)', water_ml as 'Вода(мл)' FROM nutrition_logs WHERE user_id = ? ORDER BY id DESC LIMIT 7",
                conn, params=(uid,)
            )
            conn.close()
            if not df_nut.empty:
                st.markdown("###### 📊 История питания (последние 7 записей)")
                st.dataframe(df_nut, use_container_width=True, hide_index=True)

    # =================================================================
    # ВКЛАДКА 4: 📚 ЛИТЕРАТУРА И БАЗА ЗНАНИЙ
    # =================================================================
    with tab_books:
        st.markdown("#### 📚 Интеллектуальная Библиотека по Блокам")

        # Объединяем книги из library_data.py с расширенным каталогом
        merged_library = DEFAULT_EXTENDED_LIBRARY.copy()
        for k, v in LIBRARY_CATALOG.items():
            if k not in merged_library:
                merged_library[k] = v
            else:
                existing_titles = {b["title"] for b in merged_library[k]}
                for item in v:
                    if item["title"] not in existing_titles:
                        merged_library[k].append(item)

        # Загружаем пользовательские статусы и заметки из БД
        conn = DatabaseManager.get_conn()
        df_bnotes = pd.read_sql_query("SELECT book_title, category, status, insight FROM book_notes WHERE user_id = ?", conn, params=(uid,))
        conn.close()
        user_book_map = {}
        for _, r in df_bnotes.iterrows():
            user_book_map[r["book_title"]] = {"status": r["status"], "insight": r["insight"], "category": r["category"]}

        with st.expander("➕ Добавить свою книгу или конспект в библиотеку"):
            nb_c1, nb_c2 = st.columns(2)
            with nb_c1:
                nb_title = st.text_input("Название книги и автор:", placeholder="Например: Искусство схемотехники — Хоровиц")
                nb_cat = st.selectbox("Блок литературы:", list(merged_library.keys()))
            with nb_c2:
                nb_status = st.selectbox("Статус чтения:", ["В процессе", "Прочитано", "В планах", "⭐ Избранное"])
                nb_insight = st.text_input("Главный инсайт / заметка:", placeholder="Ключевая мысль книги...")
            if st.button("📚 Сохранить книгу в мою базу", use_container_width=True):
                if nb_title.strip():
                    conn = DatabaseManager.get_conn()
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO book_notes (user_id, book_title, category, status, insight, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (uid, nb_title.strip(), nb_cat, nb_status, nb_insight.strip(), str(date.today()))
                    )
                    conn.commit()
                    conn.close()
                    st.success("✅ Книга и инсайт сохранены!")
                    st.rerun()

        selected_lib_cat = st.radio("Выбери блок литературы:", list(merged_library.keys()), horizontal=True)
        books_in_cat = merged_library.get(selected_lib_cat, [])

        # Добавляем кастомные книги пользователя для этой категории
        for b_title, b_info in user_book_map.items():
            if b_info["category"] == selected_lib_cat and b_title not in {x["title"] for x in books_in_cat}:
                books_in_cat.append({
                    "title": b_title,
                    "author": "Личная полка",
                    "status": b_info["status"],
                    "desc": b_info["insight"] or "Добавлено пользователем"
                })

        bk_col1, bk_col2 = st.columns(2)
        for idx, book in enumerate(books_in_cat):
            target_bk_col = bk_col1 if idx % 2 == 0 else bk_col2
            b_title = book["title"]
            saved_state = user_book_map.get(b_title, {})
            cur_status = saved_state.get("status", book.get("status", "В планах"))
            cur_insight = saved_state.get("insight", "")

            if "Прочитано" in cur_status:
                badge_col = "#3fb950"
            elif "процессе" in cur_status:
                badge_col = "#58a6ff"
            elif "Избранное" in cur_status:
                badge_col = "#f1e05a"
            else:
                badge_col = "#8b949e"

            with target_bk_col:
                st.markdown(f"""
                <div class="book-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
                        <div>
                            <h4 style="margin:0; font-size:17px;">📖 {b_title}</h4>
                            <span style="font-size:13px; color:#58a6ff;">✍️ {book.get('author', '')}</span>
                        </div>
                        <span class="hud-pill" style="border-color:{badge_col}; color:{badge_col}; font-size:12px;">{cur_status}</span>
                    </div>
                    <p style="margin:10px 0 0 0; font-size:13px; color:#c9d1d9; line-height:1.5;">{book.get('desc', '')}</p>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"📝 Изменить статус / заметку: {b_title[:28]}..."):
                    status_options = ["Прочитано", "В процессе", "В планах", "⭐ Избранное"]
                    st_idx = status_options.index(cur_status) if cur_status in status_options else 2
                    new_st = st.selectbox("Статус", status_options, index=st_idx, key=f"bk_st_{selected_lib_cat}_{idx}")
                    new_ins = st.text_area("Мои выписки и мысли по книге:", value=cur_insight, key=f"bk_ins_{selected_lib_cat}_{idx}", height=70)
                    if st.button("Сохранить", key=f"bk_btn_{selected_lib_cat}_{idx}", use_container_width=True):
                        conn = DatabaseManager.get_conn()
                        c = conn.cursor()
                        c.execute("DELETE FROM book_notes WHERE user_id = ? AND book_title = ?", (uid, b_title))
                        c.execute(
                            "INSERT INTO book_notes (user_id, book_title, category, status, insight, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (uid, b_title, selected_lib_cat, new_st, new_ins.strip(), str(date.today()))
                        )
                        conn.commit()
                        conn.close()
                        st.success("Обновлено!")
                        st.rerun()

    # =================================================================
    # ВКЛАДКА 5: 🎯 ЦЕЛИ (ПОЛНАЯ ВЕРСИЯ НА МЕСЯЦ И ГОД С УДАЛЕНИЕМ)
    # =================================================================
    with tab_goals:
        st.markdown("#### 🎯 Глобальные Цели на Месяц и Год")
        with st.expander("➕ Добавить новую цель"):
            new_period = st.selectbox("Период", ["Месяц", "Год"])
            p_val = "month" if new_period == "Месяц" else "year"
            new_title = st.text_input("Название цели", placeholder="Например: Сдать экзамен на 90+ / Выжать 105 кг")
            new_target = st.number_input("Целевое значение", min_value=1.0, value=100.0, step=1.0)
            new_unit = st.text_input("Единица измерения", value="шт")
            
            if st.button("🚀 Создать цель", use_container_width=True):
                if new_title.strip():
                    conn = DatabaseManager.get_conn()
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO user_goals (user_id, goal_period, goal_title, target_value, current_value, unit) VALUES (?, ?, ?, ?, 0.0, ?)",
                        (uid, p_val, new_title.strip(), new_target, new_unit.strip())
                    )
                    conn.commit()
                    conn.close()
                    st.success("✅ Новая цель добавлена!")
                    st.rerun()
                else:
                    st.warning("Введите название цели!")

        goals_df = DatabaseManager.get_goals(uid)
        col_m, col_y = st.columns(2)

        with col_m:
            st.markdown("### 📅 Цели на Месяц")
            if goals_df is not None and not goals_df.empty:
                month_goals = goals_df[goals_df["goal_period"] == "month"]
                for _, row in month_goals.iterrows():
                    gid = row["id"]
                    title = row["goal_title"]
                    target = row["target_value"]
                    curr = row["current_value"]
                    unit = row["unit"]
                    pct = min(100, int(round((curr / target) * 100)))

                    st.markdown(f"**{title}** ({curr} / {target} {unit}) — **{pct}%**")
                    st.progress(pct / 100.0)

                    col_upd, col_del = st.columns([3, 1])
                    with col_upd:
                        new_val = st.number_input(f"Обновить: {title}", value=float(curr), key=f"goal_inp_{gid}", step=1.0, label_visibility="collapsed")
                        if new_val != curr:
                            DatabaseManager.update_goal_progress(gid, new_val)
                            st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"del_goal_{gid}", help="Удалить цель"):
                            conn = DatabaseManager.get_conn()
                            c = conn.cursor()
                            c.execute("DELETE FROM user_goals WHERE id = ?", (gid,))
                            conn.commit()
                            conn.close()
                            st.success("Цель удалена!")
                            st.rerun()
                    st.divider()

        with col_y:
            st.markdown("### 🏆 Цели на Год")
            if goals_df is not None and not goals_df.empty:
                year_goals = goals_df[goals_df["goal_period"] == "year"]
                for _, row in year_goals.iterrows():
                    gid = row["id"]
                    title = row["goal_title"]
                    target = row["target_value"]
                    curr = row["current_value"]
                    unit = row["unit"]
                    pct = min(100, int(round((curr / target) * 100)))

                    st.markdown(f"**{title}** ({curr} / {target} {unit}) — **{pct}%**")
                    st.progress(pct / 100.0)

                    col_upd, col_del = st.columns([3, 1])
                    with col_upd:
                        new_val = st.number_input(f"Обновить: {title}", value=float(curr), key=f"goal_inp_{gid}", step=10.0, label_visibility="collapsed")
                        if new_val != curr:
                            DatabaseManager.update_goal_progress(gid, new_val)
                            st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"del_goal_{gid}", help="Удалить цель"):
                            conn = DatabaseManager.get_conn()
                            c = conn.cursor()
                            c.execute("DELETE FROM user_goals WHERE id = ?", (gid,))
                            conn.commit()
                            conn.close()
                            st.success("Цель удалена!")
                            st.rerun()
                    st.divider()

    # =================================================================
    # ВКЛАДКА 6: 🏆 100 ТРОФЕЕВ (С ФИЛЬТРАЦИЕЙ ПО КАТЕГОРИЯМ И СТАТУСУ)
    # =================================================================
    with tab_ach:
        st.markdown("#### 🏆 Зал Славы: 100 Легендарных Трофеев")
        ach_catalog = CoreEngine.evaluate_and_sync_achievements(
            uid, df_logs, df_rpg, 3, False, 5.0, 7.5, 8, 75, 70, 100, 3, 5, 20, 1, ""
        )
        unlocked_count = sum(1 for a in ach_catalog if a["unlocked"])
        st.progress(unlocked_count / max(1, len(ach_catalog)), text=f"Открыто трофеев: {unlocked_count} из {len(ach_catalog)}")

        flt_c1, flt_c2 = st.columns(2)
        all_cats = ["Все категории"] + sorted(list({a.get("category", "Разное") for a in ach_catalog}))
        with flt_c1:
            sel_cat = st.selectbox("Фильтр по категории:", all_cats)
        with flt_c2:
            sel_status = st.selectbox("Статус трофеев:", ["Все трофеи", "✅ Только открытые", "🔒 Только закрытые"])

        filtered_ach = []
        for a in ach_catalog:
            if sel_cat != "Все категории" and a.get("category") != sel_cat:
                continue
            if sel_status == "✅ Только открытые" and not a["unlocked"]:
                continue
            if sel_status == "🔒 Только закрытые" and a["unlocked"]:
                continue
            filtered_ach.append(a)

        ac1, ac2 = st.columns(2)
        for i, ach in enumerate(filtered_ach):
            target_col = ac1 if i % 2 == 0 else ac2
            css_cls = "ach-card ach-unlocked" if ach["unlocked"] else "ach-card ach-locked"
            status_ico = f"✅ {ach['date']}" if ach["unlocked"] else "🔒 ЗАКРЫТО"
            with target_col:
                st.markdown(f"""
                <div class="{css_cls}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:16px; font-weight:700;">{ach['icon']} {ach['title']}</span>
                        <span class="hud-pill">{status_ico}</span>
                    </div>
                    <p style="margin:6px 0 0 0; font-size:12px; color:#8b949e;">{ach.get('category', '')} • {ach['desc']}</p>
                </div>
                """, unsafe_allow_html=True)

    # =================================================================
    # ВКЛАДКА 7: 🧘 РЕЗЕТ (ВСЕ 4 ТАЙМЕРА + POMODORO ГИПЕРФОКУСА)
    # =================================================================
    with tab_sos:
        st.markdown("#### 🧘 Нейро-Резет: Восстановление и Антистресс")
        recovery_advice = CoreEngine.generate_recovery_advice(df_logs)
        st.info(recovery_advice)
        st.divider()

        st.markdown("#### ⏱️ Интерактивные протоколы разгрузки")
        rc1, rc2 = st.columns(2)

        with rc1:
            st.markdown("##### 👁️ Таймер Пальминга (60 сек)")
            if st.button("▶️ Запустить Пальминг", use_container_width=True, type="primary"):
                bar = st.progress(0, text="Закрой глаза... Расслабься...")
                status_box = st.empty()
                for sec in range(1, 61):
                    status_box.markdown(
                        f'<div class="breath-box">👁️ Восстановление: <b>{60 - sec} сек</b></div>',
                        unsafe_allow_html=True
                    )
                    bar.progress(sec / 60.0)
                    time.sleep(1)
                status_box.markdown(
                    '<div class="breath-box" style="border-color:#3fb950; background:rgba(63,185,80,0.2);">'
                    '✅ Пальминг завершен! Глаза отдохнули.</div>',
                    unsafe_allow_html=True
                )

            st.markdown("##### 🔭 Правило 20-20-20")
            if st.button("▶️ Запустить 20 сек паузу", use_container_width=True):
                b_box = st.empty()
                p_bar = st.progress(0)
                for s in range(20, 0, -1):
                    b_box.markdown(
                        f'<div class="breath-box" style="border-color:#3fb950;">🔭 Смотри вдаль!<br><span style="font-size:24px;">{s} с</span></div>',
                        unsafe_allow_html=True
                    )
                    p_bar.progress((20 - s) / 20.0)
                    time.sleep(1)
                b_box.markdown(
                    '<div class="breath-box" style="border-color:#3fb950;">✅ Фокус сброшен!</div>',
                    unsafe_allow_html=True
                )

        with rc2:
            st.markdown("##### 🌬️ Дыхание 4-7-8")
            if st.button("▶️ Запустить 4-7-8", use_container_width=True):
                breath_placeholder = st.empty()
                b_bar = st.progress(0)
                phases = [
                    ("🟢 ВДОХ НОСОМ (4 сек)", 4, "#3fb950"),
                    ("🟡 ЗАДЕРЖКА (7 сек)", 7, "#d29922"),
                    ("🔵 ВЫДОХ РТОМ (8 сек)", 8, "#58a6ff")
                ]
                total_sec = 19
                elapsed = 0
                for label, duration, col in phases:
                    for s in range(duration, 0, -1):
                        elapsed += 1
                        breath_placeholder.markdown(
                            f'<div class="breath-box" style="border-color:{col};">'
                            f'{label}<br><span style="font-size:24px;">{s} с</span></div>',
                            unsafe_allow_html=True
                        )
                        b_bar.progress(elapsed / total_sec)
                        time.sleep(1)
                breath_placeholder.markdown(
                    '<div class="breath-box" style="border-color:#3fb950;">✨ Цикл завершен!</div>',
                    unsafe_allow_html=True
                )

            st.markdown("##### 📦 Коробчатое дыхание")
            if st.button("▶️ Запустить Box Breathing", use_container_width=True):
                box_ph = st.empty()
                box_bar = st.progress(0)
                box_steps = [
                    ("🟢 Вдох (4с)", 4),
                    ("🟡 Задержка (4с)", 4),
                    ("🔵 Выдох (4с)", 4),
                    ("🟣 Задержка (4с)", 4)
                ]
                box_total = 16
                box_elapsed = 0
                for label, dur in box_steps:
                    for s in range(dur, 0, -1):
                        box_elapsed += 1
                        box_ph.markdown(
                            f'<div class="breath-box" style="border-color:#58a6ff;">{label}<br><span style="font-size:24px;">{s} с</span></div>',
                            unsafe_allow_html=True
                        )
                        box_bar.progress(box_elapsed / box_total)
                        time.sleep(1)
                box_ph.markdown(
                    '<div class="breath-box" style="border-color:#3fb950;">⚡ Фокус на максимум!</div>',
                    unsafe_allow_html=True
                )

    # =================================================================
    # ВКЛАДКА 8: 📄 ОТЧЕТ, ЭКСПОРТ В ФАЙЛ & ЛИДЕРБОРД
    # =================================================================
    with tab_rep:
        rep_c1, rep_c2 = st.columns([1.1, 1])
        with rep_c1:
            st.markdown("#### 📄 Официальная сводка & Экспорт")
            base_report = CoreEngine.generate_weekly_report(uname, is_pro, df_logs, df_rpg)
            extended_summary = (
                f"\n\n2. RPG-ПРОГРЕСС И СВЕТОФОР СТРИКОВ:\n"
                f"• Текущий уровень: LVL {player_lvl} ({cyber_title})\n"
                f"• Накоплено опыта: {hist_xp} XP\n"
                f"• Активный стрик: {streak_data['streak']} дн.\n"
                f"• Статистика за 30 дн.: 🟢 {streak_data['green']} | 🟡 {streak_data['yellow']} | 🔴 {streak_data['red']}\n"
                f"• Закрытие недели: {streak_data['week_pct']}% | Закрытие месяца: {streak_data['month_pct']}%\n"
            )
            full_report_text = base_report + extended_summary
            st.text_area("Предпросмотр:", value=full_report_text, height=260)

            dl_c1, dl_c2 = st.columns(2)
            with dl_c1:
                st.download_button(
                    label="📥 Скачать отчет (.TXT)",
                    data=full_report_text,
                    file_name=f"NeuroGuard_Report_{uname}_{date.today()}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    type="primary"
                )
            with dl_c2:
                st.download_button(
                    label="📑 Скачать отчет (.MD)",
                    data=f"# {full_report_text}",
                    file_name=f"NeuroGuard_Report_{uname}_{date.today()}.md",
                    mime="text/markdown",
                    use_container_width=True
                )

        with rep_c2:
            st.markdown("#### 🏅 Глобальный Лидерборд")
            df_leader = DatabaseManager.get_leaderboard()
            if df_leader is not None and not df_leader.empty:
                st.dataframe(df_leader, use_container_width=True, hide_index=True)
            else:
                st.info("Пока нет участников в таблице лидеров.")
