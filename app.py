# =====================================================================
# ЧАСТЬ 1 ИЗ 2: ФУНДАМЕНТ, СТИЛИ, МАНИФЕСТ, ХАБ, БИО И ДЕЙСТВИЯ
# =====================================================================
import time
import json
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

from database import DatabaseManager
from engine import CoreEngine
from library_data import LIBRARY_CATALOG, SKINS_CATALOG, WORKOUT_PROTOCOLS

# --- 1. НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(
    page_title="NeuroGuard OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

DatabaseManager.init_db()


# --- 2. ИНИЦИАЛИЗАЦИЯ ВСЕХ РАСШИРЕННЫХ ТАБЛИЦ БД ---
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS manifesto_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            log_date TEXT,
            intent_text TEXT,
            key_priority TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS pr_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            record_title TEXT,
            record_value REAL,
            record_unit TEXT,
            achieved_date TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS countdown_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_title TEXT,
            target_date TEXT,
            category TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS quick_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            created_at TEXT,
            tag TEXT,
            content TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER,
            setting_key TEXT,
            setting_value TEXT,
            PRIMARY KEY (user_id, setting_key)
        )
    """)
    conn.commit()
    conn.close()


init_extended_tables()

# --- 3. ЖЕЛЕЗОБЕТОННОЕ СОХРАНЕНИЕ СЕССИИ ПРИ ОБНОВЛЕНИИ (F5) ---
if "page" not in st.session_state:
    st.session_state.page = "landing"

if "current_user" not in st.session_state:
    st.session_state.current_user = None

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


# --- 4. ПОЛУЧЕНИЕ АКТИВНОГО СКИНА И НАСТРОЕК ---
def get_user_setting(uid: int, key: str, default_val: str) -> str:
    conn = DatabaseManager.get_conn()
    c = conn.cursor()
    c.execute("SELECT setting_value FROM user_settings WHERE user_id = ? AND setting_key = ?", (uid, key))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default_val


def set_user_setting(uid: int, key: str, val: str):
    conn = DatabaseManager.get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO user_settings (user_id, setting_key, setting_value) VALUES (?, ?, ?)",
        (uid, key, val)
    )
    conn.commit()
    conn.close()


active_skin_key = "cyber_blue"
if st.session_state.current_user:
    saved_sk = get_user_setting(st.session_state.current_user["id"], "active_skin", "cyber_blue")
    if saved_sk in SKINS_CATALOG:
        active_skin_key = saved_sk

active_skin = SKINS_CATALOG[active_skin_key]
accent_col = active_skin["accent"]
glow_col = active_skin["glow"]
bg_main = "#05070b"
border_col = "rgba(255, 255, 255, 0.1)"
text_col = "#f0f6fc"

# --- 5. ПРЕМИАЛЬНЫЙ CSS (ФИКС _arrow_right + ПЕРЕНОСЫ СЛОВ + СКИНЫ) ---
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
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        border-radius: 12px !important;
    }}
    div[data-baseweb="select"] > div:focus-within, input:focus, textarea:focus {{
        border-color: {accent_col} !important;
        box-shadow: 0 0 12px {glow_col} !important;
    }}

    /* Полное устранение бага _arrow_right в экспандерах на мобильных устройствах */
    [data-testid="stExpanderToggleIcon"],
    .streamlit-expanderHeader svg,
    details summary span[data-testid="stMarkdownContainer"] + span {{
        display: none !important;
    }}
    details > summary {{
        list-style: none !important;
        background: rgba(15, 23, 40, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
        font-weight: 600 !important;
    }}
    details > summary::-webkit-details-marker {{
        display: none !important;
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
        padding: 6px 15px;
        font-size: 13px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.35);
    }}
    .pro-pill {{
        border: 1px solid rgba(241,224,90,0.5) !important;
        background: linear-gradient(135deg, rgba(241,224,90,0.22), rgba(15,23,40,0.95)) !important;
        color: #f1e05a !important;
    }}
    .hyperfocus-pill {{
        border: 1px solid #ffd700 !important;
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.3), rgba(255, 140, 0, 0.18)) !important;
        color: #ffd700 !important;
        box-shadow: 0 0 22px rgba(255, 215, 0, 0.35) !important;
    }}
    .bento-card {{
        background: linear-gradient(180deg, rgba(15, 23, 40, 0.78) 0%, rgba(8, 12, 22, 0.92) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 14px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        word-break: normal !important;
        overflow-wrap: break-word !important;
    }}
    .bento-card:hover {{
        border-color: {accent_col}88;
    }}
    .hero-skin-card {{
        background: radial-gradient(circle at 50% 0%, {glow_col} 0%, rgba(12, 18, 32, 0.95) 75%);
        border: 1px solid {accent_col};
        border-radius: 22px;
        padding: 26px 20px;
        text-align: center;
        box-shadow: 0 0 35px {glow_col};
        margin-bottom: 14px;
    }}
    .book-card {{
        background: linear-gradient(180deg, rgba(16, 24, 42, 0.85) 0%, rgba(9, 14, 24, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 12px;
        word-break: normal !important;
        overflow-wrap: break-word !important;
    }}
    .ach-card {{
        background: rgba(15, 23, 40, 0.75);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid {border_col};
        transition: all 0.25s ease;
    }}
    .ach-unlocked {{
        border: 1px solid rgba(63, 185, 80, 0.65) !important;
        background: linear-gradient(135deg, rgba(63,185,80,0.18), rgba(15,23,40,0.92)) !important;
        box-shadow: 0 0 22px rgba(63, 185, 80, 0.18);
    }}
    .ach-locked {{
        opacity: 0.38;
    }}
    .breath-box {{
        border-radius: 18px;
        padding: 24px;
        text-align: center;
        font-size: 21px;
        font-weight: 700;
        margin: 12px 0;
        border: 2px solid {accent_col};
        background: {glow_col};
        backdrop-filter: blur(12px);
    }}
    .manifesto-modal {{
        background: linear-gradient(145deg, rgba(16, 25, 45, 0.96), rgba(7, 11, 20, 0.98));
        border: 1px solid {accent_col};
        border-radius: 24px;
        padding: 32px 26px;
        box-shadow: 0 0 50px {glow_col};
        margin: 20px auto;
        max-width: 720px;
    }}
    .saas-hero {{
        text-align: center;
        padding: 45px 20px 20px 20px;
    }}
    .system-footer {{
        text-align: center;
        font-size: 13px;
        color: #8b949e;
        margin-top: 50px;
        padding: 26px;
        border-top: 1px solid {border_col};
    }}
    </style>
""", unsafe_allow_html=True)


# --- 6. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_status_title(lvl: int):
    if lvl >= 25:
        return "Визионер Сингулярности", "#ffd700"
    elif lvl >= 20:
        return "Мастер Системы (Ранг S)", "#a371f7"
    elif lvl >= 15:
        return "Архитектор Фокуса", "#3fb950"
    elif lvl >= 10:
        return "Лидер Продуктивности (Ранг A)", "#ff7b72"
    elif lvl >= 5:
        return "Практик Потока (Ранг B)", "#58a6ff"
    elif lvl >= 2:
        return "Искатель (Ранг C)", "#79c0ff"
    return "Старт Системы", "#8b949e"


def calculate_traffic_light_streaks(df_rpg: pd.DataFrame):
    if df_rpg is None or df_rpg.empty or "log_date" not in df_rpg.columns:
        return {"streak": 0, "green": 0, "yellow": 0, "red": 0, "week_pct": 0, "month_pct": 0, "history": []}

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

    for _ in range(365):
        if check_d in date_map:
            if date_map[check_d] >= 50:
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
    for i in range(30):
        d = today_d - timedelta(days=i)
        if d in date_map:
            p = date_map[d]
            if p >= 85:
                green += 1
                history_records.append({"date": str(d), "pct": p, "status": "🟢 Отлично", "color": "#3fb950"})
            elif p >= 50:
                yellow += 1
                history_records.append({"date": str(d), "pct": p, "status": "🟡 В темпе", "color": "#d29922"})
            else:
                red += 1
                history_records.append({"date": str(d), "pct": p, "status": "🔴 Низко", "color": "#f85149"})
        else:
            red += 1
            history_records.append({"date": str(d), "pct": 0, "status": "🔴 Пропуск", "color": "#f85149"})

    logged_week = [date_map[today_d - timedelta(days=i)] for i in range(7) if (today_d - timedelta(days=i)) in date_map]
    logged_month = [date_map[today_d - timedelta(days=i)] for i in range(30) if (today_d - timedelta(days=i)) in date_map]

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


def export_full_backup_json(uid: int) -> str:
    conn = DatabaseManager.get_conn()
    backup_payload = {"exported_at": str(datetime.now()), "user_id": uid, "tables": {}}
    tables = [
        "health_logs", "rpg_logs", "user_goals", "user_achievements",
        "energy_logs", "nutrition_logs", "book_notes", "custom_quests",
        "manifesto_logs", "pr_records", "countdown_events", "quick_notes"
    ]
    for tbl in tables:
        try:
            df_t = pd.read_sql_query(f"SELECT * FROM {tbl} WHERE user_id = ?", conn, params=(uid,))
            backup_payload["tables"][tbl] = df_t.to_dict(orient="records")
        except Exception:
            backup_payload["tables"][tbl] = []
    conn.close()
    return json.dumps(backup_payload, ensure_ascii=False, indent=2)


# =====================================================================
# ЭКРАН 1: 🌟 ПРЕМИАЛЬНЫЙ СААС-ЛЕНДИНГ
# =====================================================================
if st.session_state.page == "landing":
    st.markdown("""
        <div class="saas-hero">
            <span class="hud-pill pro-pill" style="margin-bottom: 20px;">⚡ Personal Performance & Biohacking OS</span>
            <h1 style="font-size: 52px; font-weight: 900; letter-spacing: -1.5px; margin-bottom: 15px; background: linear-gradient(135deg, #ffffff 20%, #58a6ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">NEUROGUARD</h1>
            <p style="font-size: 18px; color: #8b949e; max-width: 640px; margin: 0 auto 30px auto; line-height: 1.6;">Единая операционная система для контроля энергии, глубокой фокусировки, спортивного прогресса и защиты от выгорания.</p>
        </div>
    """, unsafe_allow_html=True)

    try:
        st.image("hero.jpg", use_container_width=True)
    except Exception:
        pass

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2, c_btn3 = st.columns([1, 1.3, 1])
    with c_btn2:
        if st.button("🚀 ОТКРЫТЬ ПЛАТФОРМУ", use_container_width=True, type="primary"):
            st.session_state.page = "auth"
            st.rerun()

    st.markdown("<br><h3 style='text-align: center; margin-bottom: 28px; font-weight: 800;'>Ключевые модули экосистемы</h3>", unsafe_allow_html=True)

    def render_bento_module(emoji, title, desc, img_file):
        st.markdown(f"""
            <div class="bento-card">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                    <span style="font-size: 26px; background: rgba(88,166,255,0.15); padding: 8px 12px; border-radius: 14px;">{emoji}</span>
                    <h3 style="margin: 0; font-size: 20px; font-weight: 800;">{title}</h3>
                </div>
                <p style="color: #8b949e; font-size: 14px; line-height: 1.6; margin-bottom: 12px;">{desc}</p>
            </div>
        """, unsafe_allow_html=True)
        try:
            st.image(img_file, use_container_width=True)
        except Exception:
            pass

    bc1, bc2 = st.columns(2)
    with bc1:
        render_bento_module(
            "🛡️", "Контроль ресурса и ЦНС",
            "Анализ сна, зрительной нагрузки и восстановления. Умный алгоритм заранее предупреждает о риске переутомления.",
            "bio.jpg"
        )
        render_bento_module(
            "🏆", "100 Достижений и Журнал Рекордов",
            "Наглядная фиксация личных максимумов в спорте, учебе, программировании и сложных проектах.",
            "trophies.jpg"
        )
    with bc2:
        render_bento_module(
            "⚡", "Персональный Хаб, Скины и Стрики",
            "Кастомизация интерфейса, утренний фокус дня и гибкая система серии без обнуления при редких паузах.",
            "rpg.jpg"
        )
        render_bento_module(
            "📚", "База Знаний и Протоколы Фокуса",
            "Подборка из 40 лучших книг с личными заметками, таймеры глубокой работы, дыхательные практики и трекер питания.",
            "reset.jpg"
        )

    st.markdown("""
        <div class="system-footer">
            🟢 System Online • Powered by SQLite & Streamlit<br>
            © 2026 NeuroGuard OS. Все права защищены.
        </div>
    """, unsafe_allow_html=True)


# =====================================================================
# ЭКРАН 2: 🔐 ОКНО ВХОДА И РЕГИСТРАЦИИ
# =====================================================================
elif st.session_state.page == "auth":
    st.markdown("<h2 style='text-align: center; margin-top: 40px;'>🔐 Вход в личный хаб</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e; margin-bottom: 30px;'>Авторизуйтесь, чтобы синхронизировать прогресс и настройки</p>", unsafe_allow_html=True)

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
                    st.rerun()


# =====================================================================
# ЭКРАН 3: ⚡ ОСНОВНАЯ РАБОЧАЯ СРЕДА (ГЛАВНЫЙ ХАБ И ПАПКИ)
# =====================================================================
elif st.session_state.page == "dashboard":
    cur_u = st.session_state.current_user
    if not cur_u:
        st.session_state.page = "auth"
        st.rerun()

    uid = cur_u["id"]
    uname = cur_u["username"]
    is_pro = cur_u["is_pro"]
    today_str = str(date.today())

    # --- ОБЯЗАТЕЛЬНОЕ УТРЕННЕЕ ВСПЛЫВАЮЩЕЕ ОКНО (DAILY MANIFESTO) ---
    conn = DatabaseManager.get_conn()
    df_manifesto = pd.read_sql_query(
        "SELECT intent_text, key_priority FROM manifesto_logs WHERE user_id = ? AND log_date = ? ORDER BY id DESC LIMIT 1",
        conn, params=(uid, today_str)
    )
    conn.close()

    if "skip_manifesto_today" not in st.session_state:
        st.session_state.skip_manifesto_today = False

    if df_manifesto.empty and not st.session_state.skip_manifesto_today:
        st.markdown(f"""
            <div class="manifesto-modal">
                <span class="hud-pill" style="border-color:{accent_col}; color:{accent_col}; margin-bottom:14px;">🌅 Настройка фокуса на день • {today_str}</span>
                <h2 style="margin: 0 0 10px 0; font-weight: 800;">Главный вектор сегодняшнего дня</h2>
                <p style="color: #8b949e; font-size: 15px; line-height: 1.5; margin-bottom: 10px;">
                    Прежде чем открыть дашборд, сформулируй одну ключевую задачу или состояние, которое сделает этот день победным.
                </p>
            </div>
        """, unsafe_allow_html=True)

        mf_c1, mf_c2, mf_c3 = st.columns([1, 2, 1])
        with mf_c2:
            m_intent = st.text_area(
                "Мое главное намерение на сегодня:",
                placeholder="Например: Спокойно решить 10 сложных задач по коду, сделать силовой блок на турнике и лечь спать до 23:00.",
                height=100
            )
            m_prio = st.selectbox(
                "Приоритетная сфера дня:",
                ["🚀 Проекты, Код и Учеба", "🦾 Спорт и Рекорды", "🧘 Восстановление и Баланс ЦНС", "🎯 Закрытие дедлайнов"]
            )
            b_m1, b_m2 = st.columns([2, 1])
            with b_m1:
                if st.button("⚡ Зафиксировать фокус и войти в Хаб (+25 XP)", use_container_width=True, type="primary"):
                    if m_intent.strip():
                        conn = DatabaseManager.get_conn()
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO manifesto_logs (user_id, log_date, intent_text, key_priority) VALUES (?, ?, ?, ?)",
                            (uid, today_str, m_intent.strip(), m_prio)
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()
                    else:
                        st.warning("Напиши хотя бы одну строчку фокуса перед стартом!")
            with b_m2:
                if st.button("Пропустить сейчас", use_container_width=True):
                    st.session_state.skip_manifesto_today = True
                    st.rerun()
        st.stop()

    todays_intent = df_manifesto.iloc[0]["intent_text"] if not df_manifesto.empty else "Держать высокий темп без суеты и перегрузок."
    todays_prio = df_manifesto.iloc[0]["key_priority"] if not df_manifesto.empty else "⚡ Сбалансированный режим"

    # --- ЗАГРУЗКА ДАННЫХ И РАСЧЕТ ПАРАМЕТРОВ ОПЕРАТОРА ---
    df_logs = DatabaseManager.load_health_logs(uid)
    df_rpg = DatabaseManager.load_rpg_logs(uid)

    hist_xp = int(df_rpg["xp_earned"].sum()) if (df_rpg is not None and not df_rpg.empty and "xp_earned" in df_rpg.columns) else 0
    player_lvl = (hist_xp // 500) + 1
    xp_in_current_lvl = hist_xp % 500
    lvl_progress_pct = xp_in_current_lvl / 500.0
    status_title, title_col = get_status_title(player_lvl)

    # Суммарные характеристики для карточки персонажа
    tot_str = int(df_rpg["str_stat"].sum()) if (df_rpg is not None and not df_rpg.empty and "str_stat" in df_rpg.columns) else 10
    tot_agi = int(df_rpg["agi_stat"].sum()) if (df_rpg is not None and not df_rpg.empty and "agi_stat" in df_rpg.columns) else 10
    tot_int = int(df_rpg["int_stat"].sum()) if (df_rpg is not None and not df_rpg.empty and "int_stat" in df_rpg.columns) else 10
    tot_dsc = int(df_rpg["dsc_stat"].sum()) if (df_rpg is not None and not df_rpg.empty and "dsc_stat" in df_rpg.columns) else 10

    last_readiness = int(df_logs.iloc[0]["readiness_score"]) if (df_logs is not None and not df_logs.empty and "readiness_score" in df_logs.columns) else 75
    last_plan_pct = int(df_rpg.iloc[0]["plan_percent"]) if (df_rpg is not None and not df_rpg.empty and "plan_percent" in df_rpg.columns) else 80

    is_hyperfocus = (last_plan_pct >= 95 and last_readiness >= 75)
    streak_data = calculate_traffic_light_streaks(df_rpg)

    # --- САЙДБАР (ПРОФИЛЬ, БЫСТРЫЙ ВЫБОР СКИНА И СВЕТОФОР) ---
    with st.sidebar:
        st.markdown(f"### {active_skin['avatar']} {uname}")
        st.markdown(f"Статус: <b style='color:{title_col};'>{status_title}</b>", unsafe_allow_html=True)
        st.progress(lvl_progress_pct, text=f"LVL {player_lvl} • {xp_in_current_lvl}/500 XP")

        # Выбор скина прямо в сайдбаре
        unlocked_skins = {k: v for k, v in SKINS_CATALOG.items() if v["min_lvl"] <= player_lvl}
        skin_keys = list(unlocked_skins.keys())
        cur_skin_idx = skin_keys.index(active_skin_key) if active_skin_key in skin_keys else 0
        chosen_skin = st.selectbox(
            "🎨 Скин персонажа:",
            options=skin_keys,
            index=cur_skin_idx,
            format_func=lambda k: f"{SKINS_CATALOG[k]['avatar']} {SKINS_CATALOG[k]['name']}"
        )
        if chosen_skin != active_skin_key:
            set_user_setting(uid, "active_skin", chosen_skin)
            st.rerun()

        st.divider()
        st.markdown("##### 🚦 Стабильность и Стрик")
        st.markdown(f"🔥 Серия: **{streak_data['streak']} дн.** *(до 3 пауз)*")
        st.markdown(f"🟢 **{streak_data['green']}** | 🟡 **{streak_data['yellow']}** | 🔴 **{streak_data['red']}**")
        st.markdown(f"Неделя: **{streak_data['week_pct']}%** • Месяц: **{streak_data['month_pct']}%**")

        st.divider()
        is_pro_toggle = st.toggle("💎 PRO-режим (+25% XP)", value=cur_u["is_pro"])
        if is_pro_toggle != cur_u["is_pro"]:
            DatabaseManager.set_pro_status(uid, is_pro_toggle)
            st.session_state.current_user["is_pro"] = is_pro_toggle
            st.rerun()

        if st.button("🌅 Изменить фокус дня", use_container_width=True):
            conn = DatabaseManager.get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM manifesto_logs WHERE user_id = ? AND log_date = ?", (uid, today_str))
            conn.commit()
            conn.close()
            st.session_state.skip_manifesto_today = False
            st.rerun()

        if st.button("🚪 Выйти из профиля", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.page = "landing"
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.rerun()

    # --- ВЕРХНЯЯ ПАНЕЛЬ HUD ---
    rank_txt, rank_col = CoreEngine.get_rank_badge(last_readiness)
    tier_pill = '<span class="hud-pill pro-pill">💎 PRO x1.25</span>' if is_pro else '<span class="hud-pill">🆓 Базовый</span>'
    focus_pill = '<span class="hud-pill hyperfocus-pill">🔥 Поток +50% XP</span>' if is_hyperfocus else f'<span class="hud-pill" style="border-color:{accent_col}; color:{accent_col};">{active_skin["avatar"]} {active_skin["name"]}</span>'

    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; margin-bottom:14px;">
        <div>
            <h3 style="margin:0; font-weight:800;">{active_skin['avatar']} {uname} <span style="font-size:15px; color:{title_col}; font-weight:600;">• {status_title}</span></h3>
        </div>
        <div class="hud-row" style="margin:0;">
            {focus_pill}
            {tier_pill}
            <span class="hud-pill" style="border-color:{rank_col}; color:{rank_col};">{rank_txt}</span>
            <span class="hud-pill">🔥 {streak_data['streak']} дн.</span>
            <span class="hud-pill">🏅 LVL {player_lvl}</span>
            <span class="hud-pill">✨ {hist_xp} XP</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- ГЛАВНЫЕ ПАПКИ НАВИГАЦИИ (ЧТОБЫ ЭКРАН НЕ БЫЛ ПЕРЕГРУЖЕН) ---
    tab_hub, tab_bio, tab_rpg, tab_train, tab_books, tab_goals, tab_sos, tab_sys = st.tabs([
        "🏠 ГЛАВНЫЙ ХАБ",
        "🛡️ БИО & ЭНЕРГИЯ",
        "⚔️ ПЛАН & ПРИВЫЧКИ",
        "🏋️ СПОРТ & РЕКОРДЫ",
        "📚 БИБЛИОТЕКА (40)",
        "🎯 ЦЕЛИ & 100 ТРОФЕЕВ",
        "🧘 ФОКУС & РЕЗЕТ",
        "⚙️ СИСТЕМА & БЭКАП"
    ])

    # =================================================================
    # ПАПКА 1: 🏠 ГЛАВНЫЙ ХАБ (ПЕРСОНАЖ, СТАТЫ, МАНИФЕСТ И ДЕДЛАЙНЫ)
    # =================================================================
    with tab_hub:
        # Плашка утреннего манифеста
        st.markdown(f"""
            <div style="background: linear-gradient(90deg, {glow_col}, rgba(15,23,40,0.4)); border-left: 4px solid {accent_col}; padding: 16px 20px; border-radius: 12px; margin-bottom: 18px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                    <span style="font-size: 12px; color: {accent_col}; text-transform: uppercase; font-weight: 800; letter-spacing: 1px;">🎯 Главный фокус на сегодня ({today_str})</span>
                    <span class="hud-pill" style="font-size:12px;">{todays_prio}</span>
                </div>
                <p style="margin: 8px 0 0 0; font-weight: 600; font-size: 18px;">«{todays_intent}»</p>
            </div>
        """, unsafe_allow_html=True)

        hub_c1, hub_c2, hub_c3 = st.columns([1.05, 1.15, 1.1])

        # Центральная карточка персонажа / скина
        with hub_c1:
            st.markdown(f"""
                <div class="hero-skin-card">
                    <div style="font-size: 64px; line-height: 1; margin-bottom: 12px;">{active_skin['avatar']}</div>
                    <span class="hud-pill" style="border-color:{accent_col}; color:{accent_col}; margin-bottom:8px;">{active_skin['role']}</span>
                    <h3 style="margin: 6px 0 2px 0; font-weight: 800;">{uname}</h3>
                    <p style="color:{title_col}; font-size:14px; font-weight:600; margin:0 0 12px 0;">{status_title} • LVL {player_lvl}</p>
                    <p style="color:#8b949e; font-size:13px; margin-bottom:14px;">{active_skin['desc']}</p>
                    <div class="hud-row" style="justify-content:center; margin:0;">
                        <span class="hud-pill">💪 STR: {tot_str}</span>
                        <span class="hud-pill">⚡ AGI: {tot_agi}</span>
                        <span class="hud-pill">🧠 INT: {tot_int}</span>
                        <span class="hud-pill">👑 DSC: {tot_dsc}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Живые метрики состояния и главные цели
        with hub_c2:
            st.markdown("#### 📊 Состояние и Прогресс")
            m1, m2 = st.columns(2)
            m1.metric("🔋 Готовность ЦНС", f"{last_readiness}%")
            m2.metric("📅 Закрытие месяца", f"{streak_data['month_pct']}%")

            st.progress(last_readiness / 100.0, text=f"Ресурс восстановления: {last_readiness}%")
            st.progress(streak_data["week_pct"] / 100.0, text=f"Темп текущей недели: {streak_data['week_pct']}%")

            st.markdown("#### 🎯 Активные ориентиры")
            goals_preview = DatabaseManager.get_goals(uid)
            if goals_preview is not None and not goals_preview.empty:
                for _, gr in goals_preview.head(3).iterrows():
                    gpct = min(100, int(round((gr["current_value"] / max(1.0, gr["target_value"])) * 100)))
                    st.markdown(f"**{gr['goal_title']}** — `{gpct}%` ({gr['current_value']}/{gr['target_value']} {gr['unit']})")
                    st.progress(gpct / 100.0)
            else:
                st.caption("Добавь глобальные цели в папке «Цели и Трофеи», чтобы видеть их прогресс здесь.")

        # Обратный отсчет до важных событий + Быстрые инсайты
        with hub_c3:
            st.markdown("#### ⏳ Обратный отсчет до событий")
            conn = DatabaseManager.get_conn()
            df_cd = pd.read_sql_query("SELECT id, event_title, target_date, category FROM countdown_events WHERE user_id = ? ORDER BY target_date ASC", conn, params=(uid,))
            conn.close()

            if not df_cd.empty:
                for _, ev in df_cd.head(3).iterrows():
                    try:
                        t_date = datetime.strptime(ev["target_date"], "%Y-%m-%d").date()
                        days_left = (t_date - date.today()).days
                        d_label = f"{days_left} дн." if days_left >= 0 else "Завершено"
                    except Exception:
                        d_label = ev["target_date"]
                    st.markdown(f"""
                        <div class="bento-card" style="padding:12px 16px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <b style="font-size:14px;">{ev['event_title']}</b><br>
                                <span style="font-size:12px; color:#8b949e;">{ev['category']} • {ev['target_date']}</span>
                            </div>
                            <span class="hud-pill" style="border-color:{accent_col}; color:{accent_col};">{d_label}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("Нет активных таймеров (экзамены, турниры, релизы).")

            with st.expander("Добавить событие или дедлайн"):
                ev_title = st.text_input("Событие", placeholder="Например: Соревнования / Профильный ЕГЭ / Релиз")
                ev_date = st.date_input("Дата события", value=date.today() + timedelta(days=30), key="ev_dt")
                ev_cat = st.selectbox("Сфера", ["Учеба и Экзамены", "Спорт и Турниры", "Проекты и Код", "Личное"])
                if st.button("Сохранить таймер", use_container_width=True):
                    if ev_title.strip():
                        conn = DatabaseManager.get_conn()
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO countdown_events (user_id, event_title, target_date, category) VALUES (?, ?, ?, ?)",
                            (uid, ev_title.strip(), str(ev_date), ev_cat)
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()

    # =================================================================
    # ПАПКА 2: 🛡️ БИО, AI-ПРЕДИКТОР & ДНЕВНИК ЭНЕРГИИ
    # =================================================================
    with tab_bio:
        col_input, col_result = st.columns([1.1, 1])
        with col_input:
            st.markdown("#### 🎛️ Мониторинг сна и нагрузки")
            log_date = st.date_input("Дата", value=date.today(), key="health_date")

            c1, c2 = st.columns(2)
            with c1:
                sleep_hours = st.slider("Сон (часы)", 0.0, 12.0, 7.5, 0.5)
                study_hours = st.slider("Экран и учеба (часы)", 0.0, 14.0, 5.0, 0.5)
                training_type = st.selectbox(
                    "Режим тренировки",
                    ["Отдых", "ОФП / Турники / Бег", "Техника / Кобудо (без контакта)", "Спарринги / Контакт"]
                )
            with c2:
                sleep_quality = st.slider("Качество сна (1-10)", 1, 10, 8)
                eye_strain = st.slider("Усталость глаз (1-10)", 1, 10, 3)
                is_rest = (training_type == "Отдых")
                training_intensity = st.slider(
                    "Тяжесть тренировки", 0, 10,
                    value=0 if is_rest else 5,
                    disabled=is_rest
                )

            head_impact = st.checkbox("Была ударная нагрузка или натуживание")
            analyze_btn = st.button("⚡ Сохранить био-статус", use_container_width=True, type="primary")

        with col_result:
            st.markdown("#### 📡 Индекс готовности и прогноз ЦНС")
            current_score = CoreEngine.calculate_readiness(
                sleep_hours, sleep_quality, study_hours, eye_strain, training_intensity, head_impact
            )

            b_rank, b_col = CoreEngine.get_rank_badge(current_score)
            st.markdown(f'<span class="hud-pill" style="border-color:{b_col};">{b_rank}</span>', unsafe_allow_html=True)
            st.metric(label="Готовность организма (Readiness)", value=f"{current_score}%")
            st.progress(current_score / 100.0)

            burnout = CoreEngine.analyze_burnout_risk(df_logs, df_rpg)
            st.markdown(f"""
            <div style="background-color:{burnout['color']}18; border:1px solid {burnout['color']}; border-radius:12px; padding:14px; margin-top:12px;">
                <b style="color:{burnout['color']};">{burnout['risk_level']}</b><br>
                <p style="margin:6px 0 0 0; font-size:13px; color:#c9d1d9;">{burnout['message']}</p>
            </div>
            """, unsafe_allow_html=True)

            if analyze_btn:
                DatabaseManager.save_health_log((
                    uid, str(log_date), sleep_hours, sleep_quality, study_hours,
                    eye_strain, training_type, training_intensity,
                    int(head_impact), current_score, burnout['message']
                ))
                st.success("Био-статус сохранен!")
                st.rerun()

        st.divider()
        st.markdown("#### ⚡ Дневник энергии и концентрации (Утро / День / Вечер)")
        en_c1, en_c2 = st.columns([1, 1.2])
        with en_c1:
            en_period = st.radio("Время замера:", ["Утро", "День", "Вечер"], horizontal=True)
            en_val = st.slider("Физический тонус (1-10)", 1, 10, 8, key="en_slider")
            foc_val = st.slider("Ясность ума и фокус (1-10)", 1, 10, 8, key="foc_slider")
            str_val = st.slider("Уровень стресса (1-10)", 1, 10, 3, key="str_slider")
            en_note = st.text_input("Заметка по самочувствию:", placeholder="Например: После разминки отличная свежесть")

            if st.button("Сохранить замер энергии", use_container_width=True):
                conn = DatabaseManager.get_conn()
                c = conn.cursor()
                c.execute(
                    "INSERT INTO energy_logs (user_id, log_date, period, energy_lvl, focus_lvl, stress_lvl, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (uid, today_str, en_period, en_val, foc_val, str_val, en_note.strip())
                )
                conn.commit()
                conn.close()
                st.success("Замер сохранен!")
                st.rerun()

        with en_c2:
            conn = DatabaseManager.get_conn()
            df_en = pd.read_sql_query(
                "SELECT log_date, period, energy_lvl, focus_lvl, stress_lvl, note FROM energy_logs WHERE user_id = ? ORDER BY id DESC LIMIT 14",
                conn, params=(uid,)
            )
            conn.close()
            if not df_en.empty:
                chart_en = df_en[["energy_lvl", "focus_lvl", "stress_lvl"]].iloc[::-1].reset_index(drop=True)
                st.line_chart(chart_en)
                st.dataframe(df_en.head(5), use_container_width=True, hide_index=True)
            else:
                st.info("Сделай первый замер энергии, чтобы отслеживать свои пики продуктивности в течение дня.")

    # =================================================================
    # ПАПКА 3: ⚔️ ПЛАН ДНЯ, ПРИВЫЧКИ И СВЕТОФОР СТРИКОВ
    # =================================================================
    with tab_rpg:
        rpg_col1, rpg_col2 = st.columns([1.1, 1])
        with rpg_col1:
            st.markdown("#### 🎯 Ежедневный чек-лист и привычки")
            rpg_date = st.date_input("Дата отчета", value=date.today(), key="rpg_date")

            conn = DatabaseManager.get_conn()
            custom_q_df = pd.read_sql_query("SELECT id, quest_text FROM custom_quests WHERE user_id = ?", conn, params=(uid,))
            conn.close()

            with st.expander("Конструктор привычек (добавить пункт в шаблон)"):
                new_q_txt = st.text_input("Новая регулярная задача:", placeholder="Например: Практика английского 25 минут")
                if st.button("Добавить в постоянный список", use_container_width=True):
                    if new_q_txt.strip():
                        conn = DatabaseManager.get_conn()
                        c = conn.cursor()
                        c.execute("INSERT INTO custom_quests (user_id, quest_text) VALUES (?, ?)", (uid, new_q_txt.strip()))
                        conn.commit()
                        conn.close()
                        st.rerun()

            base_quests = [
                "Силовой блок (100 подтягиваний / ОФП)",
                "Решение 5+ профильных задач (ЕГЭ / Python)",
                "Чтение 20+ страниц книги",
                "Техническая работа / растяжка (5 раундов)"
            ]
            if not custom_q_df.empty:
                base_quests.extend(custom_q_df["quest_text"].tolist())

            default_plan = "\n".join(base_quests)
            plan_text = st.text_area("План на день:", value=default_plan, height=110)

            tasks_list = [t.strip() for t in plan_text.split("\n") if t.strip()]
            completed_tasks = 0
            if tasks_list:
                for idx, task_item in enumerate(tasks_list):
                    if st.checkbox(f"{task_item}", key=f"task_chk_{idx}"):
                        completed_tasks += 1
                plan_percent = int(round((completed_tasks / len(tasks_list)) * 100))
            else:
                plan_percent = 70

            rc1, rc2 = st.columns(2)
            with rc1:
                exercises_reps = st.number_input("Повторения (силовые / ОФП)", 0, 3000, 100, 10)
                agility_drills = st.number_input("Раунды (техника / кардио)", 0, 50, 5, 1)
                book_pages = st.number_input("Прочитано страниц", 0, 500, 20, 5)
            with rc2:
                topics_learned = st.number_input("Разобрано тем", 0, 20, 1, 1)
                tasks_solved = st.number_input("Решено задач / кейсов", 0, 200, 5, 1)

            daily_note = st.text_input("Итог или главный инсайт дня:", placeholder="Что сегодня получилось лучше всего?")
            save_rpg_btn = st.button("⚔️ Зафиксировать результат дня", use_container_width=True, type="primary")

        with rpg_col2:
            st.markdown("#### 🧬 Начисление опыта и статистика серии")
            str_pts, agi_pts, int_pts, dsc_pts, total_actions, xp_earned = CoreEngine.calculate_rpg_stats(
                exercises_reps, agility_drills, book_pages, topics_learned, tasks_solved, plan_percent, is_pro=is_pro
            )

            mode_status_str = "Стабильный темп"
            if plan_percent == 100:
                xp_earned = int(round(xp_earned * 1.5))
                mode_status_str = "🔥 Поток (+50% XP)"
                st.success("🔥 **100% выполнение плана!** Активирован бонус потока: **+50% к опыту за день**.")
            elif plan_percent < 50:
                xp_earned = max(0, xp_earned - 50)
                mode_status_str = "⚠️ Спад темпа (-50 XP)"
                st.warning("Выполнено менее половины плана (-50 XP). Серия сохраняется, если пауза не превышает 3 дней подряд.")

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

            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("🟢 Сильные дни", f"{streak_data['green']}")
            sc2.metric("🟡 Рабочие дни", f"{streak_data['yellow']}")
            sc3.metric("🔴 Паузы", f"{streak_data['red']}")

            st.progress(streak_data["week_pct"] / 100.0, text=f"Закрытие недели: {streak_data['week_pct']}%")
            st.progress(streak_data["month_pct"] / 100.0, text=f"Закрытие месяца: {streak_data['month_pct']}%")

            if save_rpg_btn:
                DatabaseManager.save_rpg_log((
                    uid, str(rpg_date), exercises_reps, agility_drills, book_pages,
                    topics_learned, tasks_solved, plan_text, plan_percent,
                    total_actions, xp_earned, str_pts, agi_pts, int_pts, dsc_pts, mode_status_str, daily_note
                ))
                st.success("Результат дня сохранен!")
                st.rerun()

        st.divider()
        st.markdown("#### 🔥 График продуктивности (GitHub-Style Heatmap)")
        if df_rpg is not None and not df_rpg.empty and "log_date" in df_rpg.columns and "plan_percent" in df_rpg.columns:
            heat_df = df_rpg[["log_date", "plan_percent"]].sort_values("log_date")
            st.bar_chart(heat_df.set_index("log_date"), color=accent_col)
        else:
            st.info("Зафиксируй первый день, чтобы построить график стабильности.")
                # =================================================================
    # ПАПКА 4: 🏋️ СПОРТ, PR-РЕКОРДЫ & ТРЕКЕР ПИТАНИЯ
    # =================================================================
    with tab_train:
        st.markdown("#### 🏋️ Тренировочный хаб, Личные рекорды и Рацион")
        sub_tr1, sub_tr2, sub_tr3 = st.tabs([
            "📋 Программы и Таймеры",
            "🏆 Журнал Рекордов (PR)",
            "🥩 Трекер Питания и Воды"
        ])

        with sub_tr1:
            tr_c1, tr_c2 = st.columns([1.15, 1])
            with tr_c1:
                st.markdown("##### Рабочие протоколы тренировок")
                w_choice = st.selectbox("Выбери направление:", list(WORKOUT_PROTOCOLS.keys()))
                steps = WORKOUT_PROTOCOLS.get(w_choice, [])
                st.markdown('<div class="bento-card">', unsafe_allow_html=True)
                for idx_s, st_text in enumerate(steps, 1):
                    st.markdown(f"**{idx_s}.** {st_text}")
                st.markdown('</div>', unsafe_allow_html=True)

            with tr_c2:
                st.markdown("##### ⏱️ Спортивные таймеры")
                tm_display = st.empty()
                tm_bar = st.progress(0)

                tc_1, tc_2, tc_3 = st.columns(3)
                with tc_1:
                    if st.button("🔥 Табата 20/10", use_container_width=True, type="primary"):
                        for s in range(20, 0, -1):
                            tm_display.markdown(f'<div class="breath-box" style="border-color:#ff7b72;">Работа: <b>{s} с</b></div>', unsafe_allow_html=True)
                            tm_bar.progress((20 - s) / 20.0)
                            time.sleep(1)
                        for s in range(10, 0, -1):
                            tm_display.markdown(f'<div class="breath-box" style="border-color:#3fb950;">Пауза: <b>{s} с</b></div>', unsafe_allow_html=True)
                            tm_bar.progress((10 - s) / 10.0)
                            time.sleep(1)
                        tm_display.markdown('<div class="breath-box" style="border-color:#3fb950;">✅ Готово!</div>', unsafe_allow_html=True)

                with tc_2:
                    if st.button("🥋 Раунд (60с)", use_container_width=True):
                        for s in range(60, 0, -1):
                            tm_display.markdown(f'<div class="breath-box" style="border-color:#d29922;">Раунд: <b>{s} с</b></div>', unsafe_allow_html=True)
                            tm_bar.progress((60 - s) / 60.0)
                            time.sleep(1)
                        tm_display.markdown('<div class="breath-box" style="border-color:#3fb950;">🔔 Гонг!</div>', unsafe_allow_html=True)

                with tc_3:
                    if st.button("💧 Отдых (45с)", use_container_width=True):
                        for s in range(45, 0, -1):
                            tm_display.markdown(f'<div class="breath-box" style="border-color:{accent_col};">Отдых: <b>{s} с</b></div>', unsafe_allow_html=True)
                            tm_bar.progress((45 - s) / 45.0)
                            time.sleep(1)
                        tm_display.markdown('<div class="breath-box" style="border-color:#3fb950;">⚡ Поход!</div>', unsafe_allow_html=True)

        with sub_tr2:
            pr_c1, pr_c2 = st.columns([1, 1.3])
            with pr_c1:
                st.markdown("##### Зафиксировать личный максимум")
                pr_cat = st.selectbox("Сфера рекорда:", ["Силовая база", "Калистеника", "Бег / Выносливость", "Учеба и Код"])
                pr_title = st.text_input("Дисциплина:", placeholder="Жим лежа / Подтягивания")
                pr_val = st.number_input("Значение:", min_value=0.0, max_value=50000.0, value=100.0)
# =================================================================
    # ПАПКА 4: 🏋️ СПОРТ, PR-РЕКОРДЫ & ТРЕКЕР ПИТАНИЯ
    # =================================================================
    with tab_train:
        st.markdown("#### 🏋️ Тренировочный хаб, Личные рекорды и Рацион")
        sub_tr1, sub_tr2, sub_tr3 = st.tabs([
            "📋 Программы и Таймеры",
            "🏆 Журнал Рекордов (PR)",
            "🥩 Трекер Питания и Воды"
        ])

        with sub_tr1:
            tr_c1, tr_c2 = st.columns([1.15, 1])
            with tr_c1:
                st.markdown("##### Рабочие протоколы тренировок")
                w_choice = st.selectbox("Выбери направление:", list(WORKOUT_PROTOCOLS.keys()))
                steps = WORKOUT_PROTOCOLS.get(w_choice, [])
                st.markdown('<div class="bento-card">', unsafe_allow_html=True)
                for idx_s, st_text in enumerate(steps, 1):
                    st.markdown(f"**{idx_s}.** {st_text}")
                st.markdown('</div>', unsafe_allow_html=True)

            with tr_c2:
                st.markdown("##### ⏱️ Спортивные таймеры")
                tm_display = st.empty()
                tm_bar = st.progress(0)

                tc_1, tc_2, tc_3 = st.columns(3)
                with tc_1:
                    if st.button("🔥 Табата 20/10", use_container_width=True, type="primary"):
                        for s in range(20, 0, -1):
                            tm_display.markdown(f'<div class="breath-box" style="border-color:#ff7b72;">Работа: <b>{s} с</b></div>', unsafe_allow_html=True)
                            tm_bar.progress((20 - s) / 20.0)
                            time.sleep(1)
                        for s in range(10, 0, -1):
                            tm_display.markdown(f'<div class="breath-box" style="border-color:#3fb950;">Пауза: <b>{s} с</b></div>', unsafe_allow_html=True)
                            tm_bar.progress((10 - s) / 10.0)
                            time.sleep(1)
                        tm_display.markdown('<div class="breath-box" style="border-color:#3fb950;">✅ Готово!</div>', unsafe_allow_html=True)

                with tc_2:
                    if st.button("🥋 Раунд (60с)", use_container_width=True):
                        for s in range(60, 0, -1):
                            tm_display.markdown(f'<div class="breath-box" style="border-color:#d29922;">Раунд: <b>{s} с</b></div>', unsafe_allow_html=True)
                            tm_bar.progress((60 - s) / 60.0)
                            time.sleep(1)
                        tm_display.markdown('<div class="breath-box" style="border-color:#3fb950;">🔔 Гонг!</div>', unsafe_allow_html=True)

                with tc_3:
                    if st.button("💧 Отдых (45с)", use_container_width=True):
                        for s in range(45, 0, -1):
                            tm_display.markdown(f'<div class="breath-box" style="border-color:{accent_col};">Отдых: <b>{s} с</b></div>', unsafe_allow_html=True)
                            tm_bar.progress((45 - s) / 45.0)
                            time.sleep(1)
                        tm_display.markdown('<div class="breath-box" style="border-color:#3fb950;">⚡ Поход!</div>', unsafe_allow_html=True)

        with sub_tr2:
            pr_c1, pr_c2 = st.columns([1, 1.3])
            with pr_c1:
                st.markdown("##### Зафиксировать личный максимум")
                pr_cat = st.selectbox("Сфера рекорда:", ["Силовая база", "Калистеника", "Бег / Выносливость", "Учеба и Код"])
                pr_title = st.text_input("Дисциплина:", placeholder="Жим лежа / Подтягивания")
                pr_val = st.number_input("Значение:", min_value=0.0, max_value=50000.0, value=100.0)
                pr_unit = st.text_input("Единицы:", value="кг")
                pr_dt = st.date_input("Дата:", value=date.today(), key="pr_dt_in")

                if st.button("🏆 Сохранить PR", use_container_width=True, type="primary"):
                    if pr_title.strip():
                        conn = DatabaseManager.get_conn()
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO pr_records (user_id, category, record_title, record_value, record_unit, achieved_date) VALUES (?, ?, ?, ?, ?, ?)",
                            (uid, pr_cat, pr_title.strip(), pr_val, pr_unit.strip(), str(pr_dt))
                        )
                        conn.commit()
                        conn.close()
                        st.success("Рекорд сохранен!")
                        st.rerun()

            with pr_c2:
                st.markdown("##### История рекордов")
                conn = DatabaseManager.get_conn()
                df_pr = pd.read_sql_query("SELECT category, record_title, record_value, record_unit, achieved_date FROM pr_records WHERE user_id = ? ORDER BY id DESC", conn, params=(uid,))
                conn.close()
                if not df_pr.empty:
                    for _, r in df_pr.iterrows():
                        st.markdown(f"""
                            <div class="bento-card" style="padding:12px 16px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                                <div><span style="font-size:11px; color:#8b949e;">{r['category']} • {r['achieved_date']}</span><br><b>{r['record_title']}</b></div>
                                <span class="hud-pill" style="border-color:{accent_col}; color:{accent_col};">{r['record_value']} {r['record_unit']}</span>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Рекорды еще не зафиксированы.")

        with sub_tr3:
            nt_c1, nt_c2 = st.columns([1, 1.2])
            with nt_c1:
                st.markdown("##### КБЖУ и Гидратация")
                nut_date = st.date_input("Дата рациона:", value=date.today(), key="n_date")
                nc1, nc2 = st.columns(2)
                with nc1:
                    cal_in = st.number_input("Ккал", 0, 6000, 2500, 100)
                    prot_in = st.number_input("Белки (г)", 0, 400, 140, 5)
                with nc2:
                    fats_in = st.number_input("Жиры (г)", 0, 300, 80, 5)
                    carbs_in = st.number_input("Углеводы (г)", 0, 800, 290, 10)
                water_in = st.slider("Вода (мл)", 0, 4500, 2200, 250)
                if st.button("Сохранить рацион", use_container_width=True, type="primary"):
                    conn = DatabaseManager.get_conn()
                    c = conn.cursor()
                    c.execute("INSERT INTO nutrition_logs (user_id, log_date, calories, protein, fats, carbs, water_ml, workout_done) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (uid, str(nut_date), cal_in, prot_in, fats_in, carbs_in, water_in, "Ок"))
                    conn.commit()
                    conn.close()
                    st.success("Сохранено!")
                    st.rerun()
            with nt_c2:
                conn = DatabaseManager.get_conn()
                df_nut = pd.read_sql_query("SELECT log_date as 'Дата', calories as 'Ккал', protein as 'Белки', water_ml as 'Вода' FROM nutrition_logs WHERE user_id = ? ORDER BY id DESC LIMIT 7", conn, params=(uid,))
                conn.close()
                if not df_nut.empty: st.dataframe(df_nut, use_container_width=True, hide_index=True)

    # =================================================================
    # ПАПКА 5: 📚 БИБЛИОТЕКА (40 КНИГ И ИНСАЙТЫ)
    # =================================================================
    with tab_books:
        st.markdown("#### 📚 База Знаний (40 книг)")
        conn = DatabaseManager.get_conn()
        df_bnotes = pd.read_sql_query("SELECT book_title, category, status, insight FROM book_notes WHERE user_id = ?", conn, params=(uid,))
        conn.close()
        user_book_map = {r["book_title"]: {"status": r["status"], "insight": r["insight"], "category": r["category"]} for _, r in df_bnotes.iterrows()}

        with st.expander("Добавить свою книгу / конспект"):
            nb_title = st.text_input("Название и автор")
            nb_cat = st.selectbox("Раздел:", list(LIBRARY_CATALOG.keys()))
            nb_status = st.selectbox("Статус:", ["В процессе", "Прочитано", "В планах", "Избранное"])
            nb_insight = st.text_input("Главная мысль / инсайт")
            if st.button("Сохранить в библиотеку", use_container_width=True):
                if nb_title.strip():
                    conn = DatabaseManager.get_conn()
                    c = conn.cursor()
                    c.execute("INSERT INTO book_notes (user_id, book_title, category, status, insight, updated_at) VALUES (?, ?, ?, ?, ?, ?)", (uid, nb_title.strip(), nb_cat, nb_status, nb_insight.strip(), today_str))
                    conn.commit()
                    conn.close()
                    st.rerun()

        selected_lib_cat = st.radio("Блок:", list(LIBRARY_CATALOG.keys()), horizontal=True)
        books_in_cat = [b.copy() for b in LIBRARY_CATALOG.get(selected_lib_cat, [])]
        for b_title, b_info in user_book_map.items():
            if b_info["category"] == selected_lib_cat and b_title not in {x["title"] for x in books_in_cat}:
                books_in_cat.append({"title": b_title, "author": "Своя", "status": b_info["status"], "desc": b_info["insight"]})

        bk_col1, bk_col2 = st.columns(2)
        for idx, book in enumerate(books_in_cat):
            target_bk_col = bk_col1 if idx % 2 == 0 else bk_col2
            b_title = book["title"]
            saved_state = user_book_map.get(b_title, {})
            cur_status = saved_state.get("status", book.get("status", "В планах"))
            cur_insight = saved_state.get("insight", "")
            with target_bk_col:
                st.markdown(f"""
                <div class="book-card">
                    <div style="display:flex; justify-content:space-between;">
                        <h4 style="margin:0; font-size:16px;">📖 {b_title}</h4>
                        <span class="hud-pill" style="font-size:11px;">{cur_status}</span>
                    </div>
                    <p style="margin:8px 0 0 0; font-size:13px; color:#c9d1d9;">{book.get('desc', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                    # =================================================================
    # ПАПКА 6: 🎯 ЦЕЛИ НА МЕСЯЦ/ГОД & 100 ТРОФЕЕВ
    # =================================================================
    with tab_goals:
        sub_g1, sub_g2 = st.tabs(["🎯 Цели на Месяц и Год", "🏆 Зал Славы (100 Трофеев)"])

        with sub_g1:
            with st.expander("Поставить новую цель"):
                new_period = st.selectbox("Период", ["Месяц", "Год"])
                p_val = "month" if new_period == "Месяц" else "year"
                new_title = st.text_input("Название цели", placeholder="Например: Сдать экзамен на 90+")
                new_target = st.number_input("Целевое значение", min_value=1.0, value=100.0)
                new_unit = st.text_input("Единица измерения", value="шт")

                if st.button("Создать цель", use_container_width=True, type="primary"):
                    if new_title.strip():
                        conn = DatabaseManager.get_conn()
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO user_goals (user_id, goal_period, goal_title, target_value, current_value, unit) VALUES (?, ?, ?, ?, 0.0, ?)",
                            (uid, p_val, new_title.strip(), new_target, new_unit.strip())
                        )
                        conn.commit()
                        conn.close()
                        st.success("Цель добавлена!")
                        st.rerun()

            goals_df = DatabaseManager.get_goals(uid)
            col_m, col_y = st.columns(2)

            with col_m:
                st.markdown("##### 📅 Цели на Месяц")
                if goals_df is not None and not goals_df.empty:
                    month_goals = goals_df[goals_df["goal_period"] == "month"]
                    for _, row in month_goals.iterrows():
                        gid, title, target, curr, unit = row["id"], row["goal_title"], row["target_value"], row["current_value"], row["unit"]
                        pct = min(100, int(round((curr / max(1.0, target)) * 100)))
                        st.markdown(f"**{title}** ({curr} / {target} {unit}) — **{pct}%**")
                        st.progress(pct / 100.0)
                        
                        uc1, uc2 = st.columns([3, 1])
                        with uc1:
                            new_val = st.number_input(f"Обновить {title}", value=float(curr), key=f"g_inp_{gid}", label_visibility="collapsed")
                            if new_val != curr:
                                DatabaseManager.update_goal_progress(gid, new_val)
                                st.rerun()
                        with uc2:
                            if st.button("🗑️", key=f"g_del_{gid}"):
                                conn = DatabaseManager.get_conn()
                                c = conn.cursor()
                                c.execute("DELETE FROM user_goals WHERE id = ?", (gid,))
                                conn.commit()
                                conn.close()
                                st.rerun()
                        st.divider()

            with col_y:
                st.markdown("##### 🏆 Цели на Год")
                if goals_df is not None and not goals_df.empty:
                    year_goals = goals_df[goals_df["goal_period"] == "year"]
                    for _, row in year_goals.iterrows():
                        gid, title, target, curr, unit = row["id"], row["goal_title"], row["target_value"], row["current_value"], row["unit"]
                        pct = min(100, int(round((curr / max(1.0, target)) * 100)))
                        st.markdown(f"**{title}** ({curr} / {target} {unit}) — **{pct}%**")
                        st.progress(pct / 100.0)
                        
                        uc1, uc2 = st.columns([3, 1])
                        with uc1:
                            new_val = st.number_input(f"Обновить {title}", value=float(curr), key=f"gy_inp_{gid}", label_visibility="collapsed")
                            if new_val != curr:
                                DatabaseManager.update_goal_progress(gid, new_val)
                                st.rerun()
                        with uc2:
                            if st.button("🗑️", key=f"gy_del_{gid}"):
                                conn = DatabaseManager.get_conn()
                                c = conn.cursor()
                                c.execute("DELETE FROM user_goals WHERE id = ?", (gid,))
                                conn.commit()
                                conn.close()
                                st.rerun()
                        st.divider()

        with sub_g2:
            ach_catalog = CoreEngine.evaluate_and_sync_achievements(
                uid, df_logs, df_rpg, 3, False, 5.0, 7.5, 8, 75, 70, 100, 3, 5, 20, 1, ""
            )
            unlocked_count = sum(1 for a in ach_catalog if a["unlocked"])
            st.progress(unlocked_count / max(1, len(ach_catalog)), text=f"Открыто трофеев: {unlocked_count} из {len(ach_catalog)}")

            flt_c1, flt_c2 = st.columns(2)
            all_cats = ["Все категории"] + sorted(list({a.get("category", "Общее") for a in ach_catalog}))
            with flt_c1:
                sel_cat = st.selectbox("Категория:", all_cats)
            with flt_c2:
                sel_status = st.selectbox("Статус:", ["Все трофеи", "Только открытые", "Только закрытые"])

            filtered_ach = [a for a in ach_catalog if (sel_cat == "Все категории" or a.get("category") == sel_cat) and not ("открытые" in sel_status and not a["unlocked"]) and not ("закрытые" in sel_status and a["unlocked"])]

            ac1, ac2 = st.columns(2)
            for i, ach in enumerate(filtered_ach):
                target_col = ac1 if i % 2 == 0 else ac2
                css_cls = "ach-card ach-unlocked" if ach["unlocked"] else "ach-card ach-locked"
                status_ico = f"✅ {ach['date']}" if ach["unlocked"] else "🔒 Закрыто"
                with target_col:
                    st.markdown(f"""
                    <div class="{css_cls}">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:15px; font-weight:700;">{ach['icon']} {ach['title']}</span>
                            <span class="hud-pill" style="font-size:11px;">{status_ico}</span>
                        </div>
                        <p style="margin:6px 0 0 0; font-size:12px; color:#8b949e;">{ach.get('category', '')} • {ach['desc']}</p>
                    </div>
                    """, unsafe_allow_html=True)

    # =================================================================
    # ПАПКА 7: 🧘 ФОКУС, РЕЗЕТ, ДЫХАНИЕ И ЗАМЕТКИ
    # =================================================================
    with tab_sos:
        st.markdown("#### 🧘 Управление состоянием, Резет и Заметки")
        recovery_advice = CoreEngine.generate_recovery_advice(df_logs)
        st.info(recovery_advice)

        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown("##### 👁️ Разгрузка зрения")
            if st.button("▶️ Пальминг (60с)", use_container_width=True, type="primary"):
                bar = st.progress(0, text="Отдых...")
                box = st.empty()
                for sec in range(1, 61):
                    box.markdown(f'<div class="breath-box">👁️ Восстановление: <b>{60 - sec} с</b></div>', unsafe_allow_html=True)
                    bar.progress(sec / 60.0)
                    time.sleep(1)
                box.markdown('<div class="breath-box" style="border-color:#3fb950;">✅ Готово!</div>', unsafe_allow_html=True)

            if st.button("▶️ Правило 20-20-20 (20с)", use_container_width=True):
                b_box = st.empty()
                p_bar = st.progress(0)
                for s in range(20, 0, -1):
                    b_box.markdown(f'<div class="breath-box" style="border-color:#3fb950;">🔭 Вдаль: <b>{s} с</b></div>', unsafe_allow_html=True)
                    p_bar.progress((20 - s) / 20.0)
                    time.sleep(1)
                b_box.markdown('<div class="breath-box" style="border-color:#3fb950;">✅ Фокус сброшен!</div>', unsafe_allow_html=True)

        with rc2:
            st.markdown("##### 🌬️ Дыхательные протоколы")
            if st.button("▶️ Дыхание 4-7-8", use_container_width=True):
                ph = st.empty()
                b_bar = st.progress(0)
                phases = [("Вдох (4с)", 4, "#3fb950"), ("Задержка (7с)", 7, "#d29922"), ("Выдох (8с)", 8, "#58a6ff")]
                elapsed = 0
                for label, duration, col in phases:
                    for s in range(duration, 0, -1):
                        elapsed += 1
                        ph.markdown(f'<div class="breath-box" style="border-color:{col};">{label}<br><b>{s} с</b></div>', unsafe_allow_html=True)
                        b_bar.progress(elapsed / 19.0)
                        time.sleep(1)
                ph.markdown('<div class="breath-box" style="border-color:#3fb950;">✨ Баланс достигнут!</div>', unsafe_allow_html=True)

            if st.button("▶️ Коробчатое дыхание 4-4-4-4", use_container_width=True):
                box_ph = st.empty()
                box_bar = st.progress(0)
                box_steps = [("Вдох (4с)", 4), ("Пауза (4с)", 4), ("Выдох (4с)", 4), ("Пауза (4с)", 4)]
                elapsed = 0
                for label, dur in box_steps:
                    for s in range(dur, 0, -1):
                        elapsed += 1
                        box_ph.markdown(f'<div class="breath-box">{label}<br><b>{s} с</b></div>', unsafe_allow_html=True)
                        box_bar.progress(elapsed / 16.0)
                        time.sleep(1)
                box_ph.markdown('<div class="breath-box" style="border-color:#3fb950;">⚡ Готовность к работе!</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown("##### 💡 Быстрые заметки и инсайты")
        qn_c1, qn_c2 = st.columns([1, 1.3])
        with qn_c1:
            qn_tag = st.selectbox("Тег:", ["Идея", "Код / Учеба", "Спорт", "Важное"])
            qn_text = st.text_area("Текст заметки:", placeholder="Запиши мысль...", height=80)
            if st.button("Сохранить заметку", use_container_width=True):
                if qn_text.strip():
                    conn = DatabaseManager.get_conn()
                    c = conn.cursor()
                    c.execute("INSERT INTO quick_notes (user_id, created_at, tag, content) VALUES (?, ?, ?, ?)", (uid, today_str, qn_tag, qn_text.strip()))
                    conn.commit()
                    conn.close()
                    st.rerun()
        with qn_c2:
            conn = DatabaseManager.get_conn()
            df_qn = pd.read_sql_query("SELECT created_at, tag, content FROM quick_notes WHERE user_id = ? ORDER BY id DESC LIMIT 5", conn, params=(uid,))
            conn.close()
            if not df_qn.empty:
                for _, nr in df_qn.iterrows():
                    st.markdown(f"""
                        <div class="bento-card" style="padding:10px 14px; margin-bottom:6px;">
                            <span style="font-size:11px; color:{accent_col};">{nr['tag']} • {nr['created_at']}</span>
                            <p style="margin:2px 0 0 0; font-size:13px;">{nr['content']}</p>
                        </div>
                    """, unsafe_allow_html=True)

    # =================================================================
    # ПАПКА 8: ⚙️ СИСТЕМА, ОТЧЕТЫ И JSON-БЭКАП
    # =================================================================
    with tab_sys:
        sys_c1, sys_c2 = st.columns([1.1, 1])

        with sys_c1:
            st.markdown("#### 📄 Официальная сводка и Бэкап")
            base_report = CoreEngine.generate_weekly_report(uname, is_pro, df_logs, df_rpg)
            extended_summary = (
                f"\n\n2. СТАТУС СИСТЕМЫ:\n"
                f"• Уровень: LVL {player_lvl} ({status_title})\n"
                f"• Опыт: {hist_xp} XP | Скин: {active_skin['name']}\n"
                f"• Серия: {streak_data['streak']} дн. (🟢 {streak_data['green']} | 🟡 {streak_data['yellow']} | 🔴 {streak_data['red']})\n"
                f"• Закрытие недели: {streak_data['week_pct']}% | Месяца: {streak_data['month_pct']}%\n"
            )
            full_report_text = base_report + extended_summary
            st.text_area("Предпросмотр отчета:", value=full_report_text, height=200)

            dl_1, dl_2 = st.columns(2)
            with dl_1:
                st.download_button("📥 Отчет (.TXT)", data=full_report_text, file_name=f"Report_{uname}_{today_str}.txt", mime="text/plain", use_container_width=True, type="primary")
            with dl_2:
                backup_json_str = export_full_backup_json(uid)
                st.download_button("💾 Бэкап (.JSON)", data=backup_json_str, file_name=f"Backup_{uname}_{today_str}.json", mime="application/json", use_container_width=True)

        with sys_c2:
            st.markdown("#### 🎨 Доступные скины интерфейса")
            for sk_key, sk_info in SKINS_CATALOG.items():
                is_open = (player_lvl >= sk_info["min_lvl"])
                badge = "✅ Открыт" if is_open else f"🔒 Нужен LVL {sk_info['min_lvl']}"
                st.markdown(f"""
                    <div class="bento-card" style="padding:10px 14px; margin-bottom:6px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <b style="color:{sk_info['accent']};">{sk_info['avatar']} {sk_info['name']}</b>
                            <span class="hud-pill" style="font-size:11px;">{badge}</span>
                        </div>
                        <p style="margin:2px 0 0 0; font-size:12px; color:#8b949e;">{sk_info['desc']}</p>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("#### 🏅 Таблица Лидеров")
            df_leader = DatabaseManager.get_leaderboard()
            if df_leader is not None and not df_leader.empty:
                st.dataframe(df_leader, use_container_width=True, hide_index=True)
