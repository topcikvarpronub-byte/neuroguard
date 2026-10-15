# ==============================================================================
# NEUROGUARD OS — ENTERPRISE PRODUCTIVITY & BIO-RHYTHM PLATFORM
# ЧАСТЬ 1 ИЗ 2: ЯДРО, СТИЛИ, БАЗА ДАННЫХ, АВТОРИЗАЦИЯ, ГЛАВНЫЙ ХАБ, БИО И ПЛАН
# ==============================================================================
import time
import json
import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

# Безопасный импорт каталогов из library_data.py с резервным фоллбэком
try:
    from library_data import LIBRARY_CATALOG, SKINS_CATALOG, WORKOUT_PROTOCOLS
except ImportError:
    SKINS_CATALOG = {
        "cyber_blue": {
            "name": "Cyber Core (Default)",
            "avatar": "⚡",
            "role": "Оператор Системы",
            "accent": "#58a6ff",
            "glow": "rgba(88, 166, 255, 0.25)",
            "min_lvl": 1,
            "desc": "Классический холодный неон в стиле Linear. Баланс фокуса и спокойствия для долгой работы."
        }
    }
    WORKOUT_PROTOCOLS = {
        "Калистеника: Сила и Горизонт": [
            "Суставная разминка + разогрев кистей и плеч — 7 мин.",
            "Статика: удержание закрытого горизонта — 5 подходов по 12 сек.",
            "Объемный блок: 100 подтягиваний за минимальное время (EMOM)."
        ]
    }
    LIBRARY_CATALOG = {"Психология & Мышление": []}

st.set_page_config(
    page_title="NeuroGuard OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 1. НАДЕЖНЫЙ МЕНЕДЖЕР БАЗЫ ДАННЫХ (SQLite)
# ==============================================================================
class DatabaseManager:
    DB_PATH = "neuroguard_os_v5.db"

    @classmethod
    def get_conn(cls):
        return sqlite3.connect(cls.DB_PATH, check_same_thread=False)

    @classmethod
    def init_db(cls):
        conn = cls.get_conn()
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                xp INTEGER DEFAULT 0,
                pro_mode INTEGER DEFAULT 1,
                active_skin TEXT DEFAULT 'cyber_blue',
                created_at TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_manifesto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                log_date TEXT,
                focus_text TEXT,
                mode_tag TEXT,
                UNIQUE(user_id, log_date)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS bio_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                log_date TEXT,
                sleep_hours REAL,
                sleep_quality INTEGER,
                screen_hours REAL,
                eye_strain INTEGER,
                workout_type TEXT,
                workout_rpe INTEGER,
                heavy_load INTEGER,
                readiness_score INTEGER,
                UNIQUE(user_id, log_date)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS energy_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                log_date TEXT,
                day_period TEXT,
                phys_tone INTEGER,
                mental_focus INTEGER,
                stress_lvl INTEGER,
                note TEXT,
                created_at TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_date TEXT,
                title TEXT,
                category TEXT,
                priority TEXT,
                xp_reward INTEGER,
                is_done INTEGER DEFAULT 0
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                category TEXT,
                xp_reward INTEGER DEFAULT 25
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                habit_id INTEGER,
                log_date TEXT,
                status INTEGER DEFAULT 1,
                UNIQUE(user_id, habit_id, log_date)
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
            CREATE TABLE IF NOT EXISTS nutrition_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                log_date TEXT,
                calories INTEGER DEFAULT 0,
                protein INTEGER DEFAULT 0,
                fats INTEGER DEFAULT 0,
                carbs INTEGER DEFAULT 0,
                water_ml INTEGER DEFAULT 0,
                UNIQUE(user_id, log_date)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS book_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                book_title TEXT,
                status TEXT,
                notes TEXT,
                rating INTEGER DEFAULT 5,
                UNIQUE(user_id, book_title)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                category TEXT,
                current_val REAL DEFAULT 0,
                target_val REAL DEFAULT 100,
                unit TEXT DEFAULT 'ед.'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS countdowns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                target_date TEXT,
                tag TEXT DEFAULT 'Старт'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS focus_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_date TEXT,
                minutes INTEGER,
                topic TEXT,
                xp_earned INTEGER
            )
        """)

        conn.commit()
        conn.close()

    @classmethod
    def ensure_defaults(cls, user_id: int):
        conn = cls.get_conn()
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM goals WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            default_goals = [
                (user_id, "Закрыть план на 100% дней", "Дисциплина", 5.0, 30.0, "дн"),
                (user_id, "Решить задач по коду/ЕГЭ", "Интеллект", 22.0, 100.0, "задач"),
                (user_id, "Сделать суммарно повторений ОФП", "Спорт", 1450.0, 10000.0, "повт")
            ]
            c.executemany(
                "INSERT INTO goals (user_id, title, category, current_val, target_val, unit) VALUES (?, ?, ?, ?, ?, ?)",
                default_goals
            )

        c.execute("SELECT COUNT(*) FROM habits WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            default_habits = [
                (user_id, "Утренняя разминка и статика (Горизонт)", "Спорт", 30),
                (user_id, "Решение задач (Проф. Математика / Python)", "Интеллект", 40),
                (user_id, "Английский язык (шаг к C1)", "Интеллект", 25),
                (user_id, "Работа над проектами (Figma / Монтаж)", "Проекты", 35),
                (user_id, "Чтение 20+ страниц без телефона", "Фокус", 25),
                (user_id, "Сон до 23:30 (Восстановление ЦНС)", "Биохакинг", 30)
            ]
            c.executemany(
                "INSERT INTO habits (user_id, title, category, xp_reward) VALUES (?, ?, ?, ?)",
                default_habits
            )

        c.execute("SELECT COUNT(*) FROM pr_records WHERE user_id = ?", (user_id,))
        if c.fetchone()[0] == 0:
            default_prs = [
                (user_id, "Калистеника", "100 подтягиваний на время", 14.0, "мин", str(date.today())),
                (user_id, "Калистеника", "Закрытый горизонт (удержание)", 15.0, "сек", str(date.today())),
                (user_id, "Силовая база", "Жим штанги лежа (цель 100)", 85.0, "кг", str(date.today()))
            ]
            c.executemany(
                "INSERT INTO pr_records (user_id, category, record_title, record_value, record_unit, achieved_date) VALUES (?, ?, ?, ?, ?, ?)",
                default_prs
            )

        conn.commit()
        conn.close()

    @classmethod
    def add_xp(cls, user_id: int, base_xp: int):
        conn = cls.get_conn()
        c = conn.cursor()
        try:
            c.execute("SELECT xp, pro_mode FROM users WHERE id = ?", (user_id,))
            row = c.fetchone()
            if row:
                curr_xp = int(row[0]) if row[0] is not None else 0
                pro = bool(row[1]) if row[1] is not None else True
                mult = 1.25 if pro else 1.0
                gain = int(round(base_xp * mult))
                new_xp = max(0, curr_xp + gain)
                c.execute("UPDATE users SET xp = ? WHERE id = ?", (new_xp, user_id))
                conn.commit()
        except Exception:
            pass
        finally:
            conn.close()


DatabaseManager.init_db()


# ==============================================================================
# 2. ВСПОМОГАТЕЛЬНЫЕ РАСЧЕТЫ (УРОВНИ, РАНГИ, RPG-СТАТЫ, READINESS)
# ==============================================================================
def get_level_data(xp: int):
    lvl = max(1, (xp // 500) + 1)
    curr_in_lvl = xp % 500
    pct = int((curr_in_lvl / 500.0) * 100)
    if lvl < 3:
        rank, status = "B-РАНГ", "Старт Системы"
    elif lvl < 7:
        rank, status = "A-РАНГ", "Адепт Дисциплины"
    elif lvl < 15:
        rank, status = "S-РАНГ", "Архитектор Фокуса"
    else:
        rank, status = "SS-РАНГ", "Монарх Продуктивности"
    return lvl, curr_in_lvl, 500, pct, rank, status


def calc_readiness(sleep_h, sleep_q, screen_h, eye_s, rpe, heavy):
    sleep_score = min(45.0, (sleep_h / 8.0) * 25.0 + (sleep_q / 10.0) * 20.0)
    fatigue_penalty = (max(0.0, screen_h - 4.0) * 1.8) + (eye_s * 1.4) + (rpe * 1.6) + (8.0 if heavy else 0.0)
    raw = 58.0 + sleep_score - fatigue_penalty
    return int(max(15, min(100, round(raw))))


def get_rpg_stats(uid: int):
    conn = DatabaseManager.get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM pr_records WHERE user_id = ?", (uid,))
    prs = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND is_done = 1", (uid,))
    done_t = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM habit_logs WHERE user_id = ? AND status = 1", (uid,))
    done_h = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(minutes), 0) FROM focus_sessions WHERE user_id = ?", (uid,))
    foc_m = c.fetchone()[0]
    conn.close()

    str_stat = 10 + prs * 2 + (done_h // 3)
    agi_stat = 10 + (done_t // 2) + (done_h // 4)
    int_stat = 10 + (foc_m // 25) + (done_t // 3)
    dsc_stat = 10 + done_h + done_t
    return str_stat, agi_stat, int_stat, dsc_stat


def get_streak_metrics(uid: int):
    conn = DatabaseManager.get_conn()
    c = conn.cursor()
    today = date.today()
    green_days, yellow_days, red_days, streak = 0, 0, 0, 0
    grace_used = 0

    for i in range(30):
        d_str = str(today - timedelta(days=i))
        c.execute("SELECT COUNT(*), COALESCE(SUM(is_done), 0) FROM tasks WHERE user_id = ? AND task_date = ?", (uid, d_str))
        t_tot, t_done = c.fetchone()
        c.execute("SELECT COUNT(*) FROM habit_logs WHERE user_id = ? AND log_date = ? AND status = 1", (uid, d_str))
        h_done = c.fetchone()[0]

        score = (t_done + h_done)
        if score >= 3:
            green_days += 1
            if i == streak + grace_used:
                streak += 1
        elif score >= 1:
            yellow_days += 1
            if i == streak + grace_used:
                streak += 1
        else:
            if i < 7:
                red_days += 1
            if i == streak + grace_used and grace_used < 3 and i > 0:
                grace_used += 1

    conn.close()
    week_pct = int(min(100, round(((green_days + yellow_days * 0.5) / 7.0) * 100)))
    month_pct = int(min(100, round(((green_days + yellow_days * 0.5) / 30.0) * 100)))
    return streak, green_days, yellow_days, red_days, week_pct, month_pct


# ==============================================================================
# 3. СЕССИЯ И ЭКРАН АВТОРИЗАЦИИ
# ==============================================================================
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "edit_manifesto" not in st.session_state:
    st.session_state.edit_manifesto = False

if st.session_state.user_id is None:
    st.markdown("""
        <style>
        .stApp { background-color: #0b0f17; color: #e6edf3; }
        .auth-box {
            max-width: 460px; margin: 60px auto 20px auto; padding: 28px;
            background: #111722; border: 1px solid #232d3f; border-radius: 16px;
            box-shadow: 0 12px 35px rgba(0,0,0,0.45); text-align: center;
        }
        </style>
        <div class="auth-box">
            <h2 style="margin-bottom:4px; color:#58a6ff;">⚡ NeuroGuard OS</h2>
            <p style="color:#8b949e; font-size:0.92rem; margin-bottom:0;">
                Персональная экосистема продуктивности, биоритмов и дисциплины
            </p>
        </div>
    """, unsafe_allow_html=True)

    c_l, c_m, c_r = st.columns([1, 1.4, 1])
    with c_m:
        auth_tab1, auth_tab2 = st.tabs(["🔑 Вход в систему", "🚀 Быстрая регистрация"])
        with auth_tab1:
            l_user = st.text_input("Логин оператора:", value="Igor_Founder", key="auth_login_user")
            l_pass = st.text_input("Пароль:", type="password", value="10012010", key="auth_login_pass")
            if st.button("Войти в терминал", use_container_width=True, type="primary", key="auth_login_btn"):
                conn = DatabaseManager.get_conn()
                c = conn.cursor()
                c.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", (l_user.strip(), l_pass.strip()))
                user_row = c.fetchone()
                if not user_row and l_user.strip() == "Igor_Founder":
                    c.execute(
                        "INSERT INTO users (username, password, xp, pro_mode, active_skin, created_at) VALUES (?, ?, 0, 1, 'cyber_blue', ?)",
                        ("Igor_Founder", l_pass.strip(), str(date.today()))
                    )
                    conn.commit()
                    c.execute("SELECT id, username FROM users WHERE username = ?", ("Igor_Founder",))
                    user_row = c.fetchone()
                conn.close()

                if user_row:
                    st.session_state.user_id = user_row[0]
                    st.session_state.username = user_row[1]
                    DatabaseManager.ensure_defaults(user_row[0])
                    st.rerun()
                else:
                    st.error("Неверный логин или пароль.")

        with auth_tab2:
            r_user = st.text_input("Новый позывной (логин):", placeholder="Например: Igor_Founder", key="auth_reg_user")
            r_pass = st.text_input("Создайте пароль:", type="password", key="auth_reg_pass")
            if st.button("Создать профиль", use_container_width=True, key="auth_reg_btn"):
                if r_user.strip() and r_pass.strip():
                    conn = DatabaseManager.get_conn()
                    c = conn.cursor()
                    try:
                        c.execute(
                            "INSERT INTO users (username, password, xp, pro_mode, active_skin, created_at) VALUES (?, ?, 0, 1, 'cyber_blue', ?)",
                            (r_user.strip(), r_pass.strip(), str(date.today()))
                        )
                        conn.commit()
                        new_id = c.lastrowid
                        conn.close()
                        DatabaseManager.ensure_defaults(new_id)
                        st.session_state.user_id = new_id
                        st.session_state.username = r_user.strip()
                        st.rerun()
                    except sqlite3.IntegrityError:
                        conn.close()
                        st.warning("Такой позывной уже занят.")
                else:
                    st.warning("Заполни логин и пароль.")
    st.stop()


# ==============================================================================
# 4. ЗАГРУЗКА ПРОФИЛЯ, СКИНА И CSS БЕЗ БАГА _arrow_right
# ==============================================================================
uid = st.session_state.user_id
uname = st.session_state.username
DatabaseManager.ensure_defaults(uid)

conn = DatabaseManager.get_conn()
c = conn.cursor()
c.execute("SELECT xp, pro_mode, active_skin FROM users WHERE id = ?", (uid,))
u_row = c.fetchone()
conn.close()

user_xp = u_row[0] if u_row else 0
pro_active = bool(u_row[1]) if u_row else True
skin_key = u_row[2] if (u_row and u_row[2] in SKINS_CATALOG) else "cyber_blue"

lvl, xp_in_lvl, xp_need, lvl_pct, u_rank, u_status = get_level_data(user_xp)
skin_cfg = SKINS_CATALOG.get(skin_key, list(SKINS_CATALOG.values())[0])
accent_col = skin_cfg["accent"]
glow_col = skin_cfg["glow"]

# ВАЖНО: В CSS мы НЕ перезаписываем font-family у span-иконок Streamlit,
# чтобы никогда не появлялся текстовый артефакт _arrow_right!
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, .stApp, p, div, h1, h2, h3, h4, h5, h6, label, input, textarea, button {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    /* Защита иконок Streamlit от поломки шрифта (_arrow_right) */
    [data-testid="stIconMaterial"], .material-icons, span[ translate="no" ] {{
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    }}

    .stApp {{
        background-color: #0b0f17;
        color: #e6edf3;
    }}
    [data-testid="stSidebar"] {{
        background-color: #0e131d !important;
        border-right: 1px solid #1f2937;
    }}
    .bento-card {{
        background: linear-gradient(145deg, #121824 0%, #0e131d 100%);
        border: 1px solid #222c3c;
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.28);
    }}
    .hero-card {{
        background: linear-gradient(160deg, #141c2b 0%, #0d121c 100%);
        border: 1px solid {accent_col};
        border-radius: 16px;
        padding: 22px 16px;
        text-align: center;
        box-shadow: 0 0 28px {glow_col};
        margin-bottom: 14px;
    }}
    .manifesto-banner {{
        background: linear-gradient(90deg, rgba(20, 28, 43, 0.95) 0%, rgba(15, 21, 33, 0.95) 100%);
        border-left: 4px solid {accent_col};
        border-top: 1px solid #232e42;
        border-right: 1px solid #232e42;
        border-bottom: 1px solid #232e42;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 18px;
    }}
    .pill-badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #2b3648;
        margin-right: 6px;
        margin-bottom: 6px;
        color: #c9d1d9;
    }}
    .pill-accent {{
        border-color: {accent_col};
        color: {accent_col};
        background: {glow_col};
    }}
    .stat-chip {{
        background: #161f2e;
        border: 1px solid #263347;
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 0.82rem;
        font-weight: 600;
        margin: 5px 0;
        display: block;
    }}
    .breath-box {{
        background: #121824;
        border: 2px solid {accent_col};
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        font-size: 1.05rem;
        margin-bottom: 10px;
    }}
    .trophy-card {{
        background: #111722;
        border: 1px solid #202938;
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 8px;
        font-size: 0.84rem;
    }}
    .trophy-unlocked {{
        border-color: {accent_col};
        background: linear-gradient(135deg, rgba(22,31,48,0.9), rgba(14,19,29,0.9));
    }}
    </style>
""", unsafe_allow_html=True)


# ==============================================================================
# 5. БОКОВАЯ ПАНЕЛЬ (SIDEBAR)
# ==============================================================================
streak_days, g_days, y_days, r_days, w_pct, m_pct = get_streak_metrics(uid)

with st.sidebar:
    st.markdown(f"### {skin_cfg['avatar']} {uname}")
    st.caption(f"Статус: **{u_status}**")
    st.markdown(f"**LVL {lvl}** • `{xp_in_lvl}/{xp_need} XP`")
    st.progress(lvl_pct / 100.0)

    st.markdown("---")
    skin_keys = list(SKINS_CATALOG.keys())
    skin_labels = [
        f"{SKINS_CATALOG[k]['avatar']} {SKINS_CATALOG[k]['name']}" + (f" (с LVL {SKINS_CATALOG[k]['min_lvl']})" if lvl < SKINS_CATALOG[k]['min_lvl'] else "")
        for k in skin_keys
    ]
    curr_skin_idx = skin_keys.index(skin_key) if skin_key in skin_keys else 0
    picked_label = st.selectbox("🎨 Скин персонажа:", skin_labels, index=curr_skin_idx, key="sb_skin_selector")
    picked_key = skin_keys[skin_labels.index(picked_label)]

    if picked_key != skin_key:
        req_lvl = SKINS_CATALOG[picked_key]["min_lvl"]
        if lvl >= req_lvl:
            conn = DatabaseManager.get_conn()
            c = conn.cursor()
            c.execute("UPDATE users SET active_skin = ? WHERE id = ?", (picked_key, uid))
            conn.commit()
            conn.close()
            st.rerun()
        else:
            st.warning(f"Этот скин открывается на {req_lvl} уровне!")

    st.markdown("---")
    st.markdown("**🚦 Стабильность и Стрик**")
    st.markdown(f"🔥 Серия: **{streak_days} дн.** *(до 3 пауз)*")
    st.markdown(f"🟢 **{g_days}** | 🟡 **{y_days}** | 🔴 **{r_days}**")
    st.caption(f"Неделя: **{w_pct}%** • Месяц: **{m_pct}%**")

    st.markdown("---")
    new_pro = st.toggle("💎 PRO-режим (+25% XP)", value=pro_active, key="sb_pro_toggle")
    if new_pro != pro_active:
        conn = DatabaseManager.get_conn()
        c = conn.cursor()
        c.execute("UPDATE users SET pro_mode = ? WHERE id = ?", (1 if new_pro else 0, uid))
        conn.commit()
        conn.close()
        st.rerun()

    if st.button("🌅 Изменить фокус дня", use_container_width=True, key="sb_edit_manifesto_btn"):
        st.session_state.edit_manifesto = not st.session_state.edit_manifesto
        st.rerun()

    if st.button("🚪 Выйти из профиля", use_container_width=True, key="sb_logout_btn"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()


# ==============================================================================
# 6. ВЕРХНИЙ ХЕДЕР И УТРЕННИЙ МАНИФЕСТ ДНЯ
# ==============================================================================
st.markdown(f"""
    <div style="margin-bottom: 12px;">
        <h2 style="margin:0; font-weight:800;">{skin_cfg['avatar']} {uname} <span style="font-size:1rem; color:#8b949e; font-weight:500;">• {u_status}</span></h2>
        <div style="margin-top:8px;">
            <span class="pill-badge pill-accent">{skin_cfg['avatar']} {skin_cfg['name']}</span>
            <span class="pill-badge">💎 {'PRO x1.25' if pro_active else 'STANDARD'}</span>
            <span class="pill-badge">⚔️ {u_rank}</span>
            <span class="pill-badge">🔥 {streak_days} дн.</span>
            <span class="pill-badge">🏅 LVL {lvl}</span>
            <span class="pill-badge">✨ {user_xp} XP</span>
        </div>
    </div>
""", unsafe_allow_html=True)

today_str = str(date.today())
conn = DatabaseManager.get_conn()
c = conn.cursor()
c.execute("SELECT focus_text, mode_tag FROM daily_manifesto WHERE user_id = ? AND log_date = ?", (uid, today_str))
man_row = c.fetchone()
conn.close()

if not man_row or st.session_state.edit_manifesto:
    st.markdown('<div class="bento-card">', unsafe_allow_html=True)
    st.markdown("##### 🌅 Настройка главного фокуса на сегодня")
    m_col1, m_col2 = st.columns([2, 1])
    with m_col1:
        f_in = st.text_input(
            "Твой главный результат дня:",
            value=man_row[0] if man_row else "Держать высокий темп без суеты и перегрузок.",
            key="manifesto_text_in"
        )
    with m_col2:
        mode_opts = ["⚡ Сбалансированный режим", "🔥 Режим Прорыва (Hardcore)", "🛡️ Бережное восстановление"]
        m_in = st.selectbox("Режим работы:", mode_opts, key="manifesto_mode_in")
    if st.button("Зафиксировать манифест дня (+15 XP)", type="primary", key="save_manifesto_btn"):
        conn = DatabaseManager.get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO daily_manifesto (user_id, log_date, focus_text, mode_tag) VALUES (?, ?, ?, ?)",
            (uid, today_str, f_in.strip(), m_in)
        )
        conn.commit()
        conn.close()
        if not man_row:
            DatabaseManager.add_xp(uid, 15)
        st.session_state.edit_manifesto = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 7. НАВИГАЦИЯ ПО 7 ОСНОВНЫМ ВКЛАДКАМ
# ==============================================================================
tab_hub, tab_bio, tab_plan, tab_train, tab_lib, tab_goals, tab_sys = st.tabs([
    "🔥 ГЛАВНЫЙ ХАБ",
    "🛡️ БИО & ЭНЕРГИЯ",
    "⚔️ ПЛАН & ПРИВЫЧКИ",
    "🏋️ СПОРТ & РЕКОРДЫ",
    "📚 БИБЛИОТЕКА (40)",
    "🎯 ЦЕЛИ & 100 ТРОФЕЕВ",
    "⚙️ СИСТЕМА & БЭКАП"
])

# ------------------------------------------------------------------------------
# ВКЛАДКА 1: ГЛАВНЫЙ ХАБ
# ------------------------------------------------------------------------------
with tab_hub:
    focus_txt = man_row[0] if man_row else "Держать высокий темп без суеты и перегрузок."
    mode_txt = man_row[1] if man_row else "⚡ Сбалансированный режим"

    st.markdown(f"""
        <div class="manifesto-banner">
            <div style="font-size:0.78rem; color:#8b949e; text-transform:uppercase; letter-spacing:0.06em;">
                🎯 ГЛАВНЫЙ ФОКУС НА СЕГОДНЯ ({today_str})
            </div>
            <div style="margin: 4px 0 8px 0;">
                <span class="pill-badge pill-accent" style="font-size:0.75rem;">{mode_txt}</span>
            </div>
            <div style="font-size:1.08rem; font-weight:700; color:#f0f6fc;">
                «{focus_txt}»
            </div>
        </div>
    """, unsafe_allow_html=True)

    str_s, agi_s, int_s, dsc_s = get_rpg_stats(uid)

    conn = DatabaseManager.get_conn()
    c = conn.cursor()
    c.execute("SELECT readiness_score FROM bio_logs WHERE user_id = ? ORDER BY log_date DESC LIMIT 1", (uid,))
    r_last = c.fetchone()
    readiness_val = r_last[0] if r_last else 72

    c.execute("SELECT COUNT(*), COALESCE(SUM(is_done), 0) FROM tasks WHERE user_id = ? AND task_date = ?", (uid, today_str))
    t_all, t_ok = c.fetchone()
    day_pct = int(round((t_ok / t_all) * 100)) if t_all > 0 else 0
    conn.close()

    col_hero, col_mid, col_cd = st.columns([1.05, 1.35, 1.1])

    with col_hero:
        st.markdown(f"""
            <div class="hero-card">
                <div style="font-size:3.2rem; line-height:1.1; margin-bottom:8px;">{skin_cfg['avatar']}</div>
                <span class="pill-badge pill-accent">{skin_cfg['role']}</span>
                <h3 style="margin:10px 0 4px 0; font-weight:800;">{uname}</h3>
                <div style="font-size:0.84rem; color:#8b949e; margin-bottom:10px;">{u_status} • LVL {lvl}</div>
                <p style="font-size:0.8rem; color:#9ca3af; line-height:1.4; margin-bottom:14px;">{skin_cfg['desc']}</p>
                <div class="stat-chip">💪 STR (Сила): {str_s}</div>
                <div class="stat-chip">⚡ AGI (Темп): {agi_s}</div>
                <div class="stat-chip">🧠 INT (Интеллект): {int_s}</div>
                <div class="stat-chip">👑 DSC (Дисциплина): {dsc_s}</div>
            </div>
        """, unsafe_allow_html=True)

    with col_mid:
        st.markdown("#### 📊 Состояние и Прогресс")
        m1, m2 = st.columns(2)
        m1.metric("🔋 Готовность ЦНС", f"{readiness_val}%")
        m2.metric("📅 Закрыто сегодня", f"{day_pct}%")

        st.caption(f"Ресурс восстановления: {readiness_val}%")
        st.progress(readiness_val / 100.0)
        st.caption(f"Темп текущей недели: {w_pct}%")
        st.progress(w_pct / 100.0)

        st.markdown("#### 🎯 Активные ориентиры")
        conn = DatabaseManager.get_conn()
        df_g = pd.read_sql_query("SELECT title, current_val, target_val, unit FROM goals WHERE user_id = ? LIMIT 3", conn, params=(uid,))
        conn.close()
        for _, gr in df_g.iterrows():
            gp = min(100, int(round((gr["current_val"] / max(1.0, gr["target_val"])) * 100)))
            st.markdown(f"**{gr['title']}** — `{gp}%` ({gr['current_val']}/{gr['target_val']} {gr['unit']})")
            st.progress(gp / 100.0)

    with col_cd:
        st.markdown("#### ⏳ Обратный отсчет до событий")
        conn = DatabaseManager.get_conn()
        df_cd = pd.read_sql_query("SELECT id, title, target_date, tag FROM countdowns WHERE user_id = ? ORDER BY target_date ASC", conn, params=(uid,))
        conn.close()

        if df_cd.empty:
            st.caption("Нет активных таймеров (экзамены, турниры, релизы).")
        else:
            for _, cdr in df_cd.iterrows():
                try:
                    t_dt = datetime.strptime(cdr["target_date"], "%Y-%m-%d").date()
                    rem_days = (t_dt - date.today()).days
                except ValueError:
                    rem_days = 0
                badge_col = "#3fb950" if rem_days > 14 else ("#d29922" if rem_days >= 0 else "#ff7b72")
                st.markdown(f"""
                    <div class="bento-card" style="padding:12px 14px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; font-size:0.92rem;">{cdr['title']}</span>
                            <span style="color:{badge_col}; font-weight:800; font-size:0.95rem;">{rem_days} дн.</span>
                        </div>
                        <div style="font-size:0.76rem; color:#8b949e; margin-top:4px;">
                            🏷️ {cdr['tag']} • Дата: {cdr['target_date']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="bento-card" style="padding:14px;">', unsafe_allow_html=True)
        st.markdown("**➕ Новый дедлайн или турнир**")
        cd_title = st.text_input("Название события:", placeholder="ЕГЭ Проф. Математика / Турнир", key="hub_cd_title_in")
        cd_date = st.date_input("Дата события:", value=date.today() + timedelta(days=30), key="hub_cd_date_in")
        cd_tag = st.selectbox("Категория:", ["Экзамен / Олимпиада", "Соревнования / Пояс", "Релиз проекта", "Личная цель"], key="hub_cd_tag_in")
        if st.button("Добавить таймер", use_container_width=True, key="hub_cd_add_btn"):
            if cd_title.strip():
                conn = DatabaseManager.get_conn()
                c = conn.cursor()
                c.execute(
                    "INSERT INTO countdowns (user_id, title, target_date, tag) VALUES (?, ?, ?, ?)",
                    (uid, cd_title.strip(), str(cd_date), cd_tag)
                )
                conn.commit()
                conn.close()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
# ==============================================================================
# ЧАСТЬ 2 ИЗ 2: БИО & ЭНЕРГИЯ, ПЛАН & ПРИВЫЧКИ, СПОРТ, БИБЛИОТЕКА, ЦЕЛИ, СИСТЕМА
# ==============================================================================

# ------------------------------------------------------------------------------
# ВКЛАДКА 2: БИО & ЭНЕРГИЯ
# ------------------------------------------------------------------------------
with tab_bio:
    st.markdown("#### 🛡️ Био-мониторинг, Готовность ЦНС и Дневник энергии")
    b_col1, b_col2 = st.columns([1.25, 1])

    with b_col1:
        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        bio_dt = st.date_input("Дата био-замера:", value=date.today(), key="bio_date_picker")

        conn = DatabaseManager.get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT sleep_hours, sleep_quality, screen_hours, eye_strain, workout_type, workout_rpe, heavy_load FROM bio_logs WHERE user_id = ? AND log_date = ?",
            (uid, str(bio_dt))
        )
        b_row = c.fetchone()
        conn.close()

        sl_c1, sl_c2 = st.columns(2)
        with sl_c1:
            sleep_h = st.slider("Сон (часы)", 3.0, 12.0, float(b_row[0]) if b_row else 7.5, 0.5, key="bio_sleep_h")
            screen_h = st.slider("Экран и учеба (часы)", 0.0, 16.0, float(b_row[2]) if b_row else 5.0, 0.5, key="bio_screen_h")
            w_opts = ["Отдых", "Калистеника / ОФП", "Каратэ / Кобудо / Самбо", "Тяжелая атлетика / Зал", "Бег / Выносливость"]
            w_idx = w_opts.index(b_row[4]) if (b_row and b_row[4] in w_opts) else 0
            w_type = st.selectbox("Режим тренировки", w_opts, index=w_idx, key="bio_w_type")

        with sl_c2:
            sleep_q = st.slider("Качество сна (1-10)", 1, 10, int(b_row[1]) if b_row else 8, key="bio_sleep_q")
            eye_s = st.slider("Усталость глаз (1-10)", 1, 10, int(b_row[3]) if b_row else 3, key="bio_eye_s")
            w_rpe = st.slider("Тяжесть тренировки (0-10)", 0, 10, int(b_row[5]) if b_row else 0, key="bio_w_rpe")

        heavy_chk = st.checkbox(
            "Была ударная нагрузка или натуживание (Вальсальва / спарринги)",
            value=bool(b_row[6]) if b_row else False,
            key="bio_heavy_chk"
        )

        calc_r = calc_readiness(sleep_h, sleep_q, screen_h, eye_s, w_rpe, heavy_chk)

        if st.button("⚡ Сохранить био-статус (+20 XP)", type="primary", use_container_width=True, key="bio_save_btn"):
            conn = DatabaseManager.get_conn()
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO bio_logs
                (user_id, log_date, sleep_hours, sleep_quality, screen_hours, eye_strain, workout_type, workout_rpe, heavy_load, readiness_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (uid, str(bio_dt), sleep_h, sleep_q, screen_h, eye_s, w_type, w_rpe, 1 if heavy_chk else 0, calc_r))
            conn.commit()
            conn.close()
            DatabaseManager.add_xp(uid, 20)
            st.success("Био-статус сохранен!")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with b_col2:
        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        st.metric("Готовность организма (Readiness)", f"{calc_r}%")
        st.progress(calc_r / 100.0)

        if calc_r >= 70 and not heavy_chk and eye_s <= 5:
            st.markdown("""
                <div style="background:rgba(63,185,80,0.12); border:1px solid #3fb950; border-radius:10px; padding:12px; margin-top:10px;">
                    <b style="color:#3fb950;">🟢 БАЛАНС И ТОНУС</b><br>
                    <span style="font-size:0.86rem;">✅ Отличный баланс работы и восстановления. Риск выгорания минимален. Можно работать на пике.</span>
                </div>
            """, unsafe_allow_html=True)
        elif calc_r >= 45:
            st.markdown("""
                <div style="background:rgba(210,153,34,0.12); border:1px solid #d29922; border-radius:10px; padding:12px; margin-top:10px;">
                    <b style="color:#d29922;">🟡 УМЕРЕННОЕ НАПРЯЖЕНИЕ</b><br>
                    <span style="font-size:0.86rem;">⚠️ Заметна нагрузка на глаза или ЦНС. Сделай упор на технику, избегай жесткого отказа и дай глазам отдых.</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background:rgba(255,123,114,0.12); border:1px solid #ff7b72; border-radius:10px; padding:12px; margin-top:10px;">
                    <b style="color:#ff7b72;">🔴 ТРЕБУЕТСЯ ВОССТАНОВЛЕНИЕ</b><br>
                    <span style="font-size:0.86rem;">🛑 Высокое утомление ЦНС. Замени тяжелую силовую на разминку, прогулку и ранний сон.</span>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### ⚡ Дневник энергии и концентрации (Утро / День / Вечер)")
    e_col1, e_col2 = st.columns([1, 1.35])

    with e_col1:
        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        e_period = st.radio("Время замера:", ["🌅 Утро", "☀️ День", "🌙 Вечер"], horizontal=True, key="en_period_rad")
        e_phys = st.slider("Физический тонус (1-10)", 1, 10, 8, key="en_phys_sl")
        e_ment = st.slider("Ясность ума и фокус (1-10)", 1, 10, 8, key="en_ment_sl")
        e_str = st.slider("Уровень стресса (1-10)", 1, 10, 3, key="en_str_sl")
        e_note = st.text_input("Заметка по самочувствию:", placeholder="Например: После разминки отличный фокус", key="en_note_in")

        if st.button("Сохранить замер энергии (+10 XP)", use_container_width=True, key="en_save_btn"):
            conn = DatabaseManager.get_conn()
            c = conn.cursor()
            c.execute("""
                INSERT INTO energy_logs (user_id, log_date, day_period, phys_tone, mental_focus, stress_lvl, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (uid, today_str, e_period, e_phys, e_ment, e_str, e_note.strip(), datetime.now().strftime("%H:%M")))
            conn.commit()
            conn.close()
            DatabaseManager.add_xp(uid, 10)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with e_col2:
        conn = DatabaseManager.get_conn()
        df_en = pd.read_sql_query(
            "SELECT log_date, day_period, phys_tone, mental_focus, stress_lvl, note FROM energy_logs WHERE user_id = ? ORDER BY id DESC LIMIT 10",
            conn, params=(uid,)
        )
        conn.close()
        if df_en.empty:
            st.info("Сделай первый замер энергии, чтобы отслеживать свои пики продуктивности в течение дня.")
        else:
            st.dataframe(df_en, use_container_width=True, hide_index=True)


# ------------------------------------------------------------------------------
# ВКЛАДКА 3: ПЛАН & ПРИВЫЧКИ
# ------------------------------------------------------------------------------
with tab_plan:
    st.markdown("#### ⚔️ Тактический планировщик задач и Матрица привычек")
    p_col1, p_col2 = st.columns([1.15, 1])

    with p_col1:
        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        st.markdown("##### 📋 Задачи на выбранный день")
        t_date = st.date_input("Дата плана:", value=date.today(), key="plan_date_picker")

        with st.container():
            nt_title = st.text_input("Новая задача:", placeholder="Например: Решить 5 задач 1 части Проф. Математики", key="plan_new_title")
            nt_c1, nt_c2 = st.columns(2)
            with nt_c1:
                nt_cat = st.selectbox("Сфера:", ["Интеллект / ЕГЭ", "Проекты / Фриланс", "Спорт / ОФП", "Личное / Режим"], key="plan_new_cat")
            with nt_c2:
                nt_prio = st.selectbox("Приоритет:", ["🔥 Высокий (40 XP)", "⚡ Средний (25 XP)", "🟢 Базовый (15 XP)"], key="plan_new_prio")

            if st.button("➕ Добавить в план", type="primary", use_container_width=True, key="plan_add_btn"):
                if nt_title.strip():
                    xp_map = {"🔥 Высокий (40 XP)": 40, "⚡ Средний (25 XP)": 25, "🟢 Базовый (15 XP)": 15}
                    conn = DatabaseManager.get_conn()
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO tasks (user_id, task_date, title, category, priority, xp_reward, is_done)
                        VALUES (?, ?, ?, ?, ?, ?, 0)
                    """, (uid, str(t_date), nt_title.strip(), nt_cat, nt_prio, xp_map[nt_prio]))
                    conn.commit()
                    conn.close()
                    st.rerun()

        st.markdown("---")
        conn = DatabaseManager.get_conn()
        df_tasks = pd.read_sql_query(
            "SELECT id, title, category, priority, xp_reward, is_done FROM tasks WHERE user_id = ? AND task_date = ? ORDER BY is_done ASC, id DESC",
            conn, params=(uid, str(t_date))
        )
        conn.close()

        if df_tasks.empty:
            st.caption("На этот день задач пока нет. Добавь 3 главных шага!")
        else:
            for _, tr in df_tasks.iterrows():
                tid = int(tr["id"])
                done_bool = bool(tr["is_done"])
                tc1, tc2 = st.columns([0.85, 0.15])
                with tc1:
                    chk = st.checkbox(
                        f"**{tr['title']}**  •  `{tr['category']}` (+{tr['xp_reward']} XP)",
                        value=done_bool,
                        key=f"task_chk_{tid}"
                    )
                    if chk != done_bool:
                        conn = DatabaseManager.get_conn()
                        c = conn.cursor()
                        c.execute("UPDATE tasks SET is_done = ? WHERE id = ?", (1 if chk else 0, tid))
                        conn.commit()
                        conn.close()
                        DatabaseManager.add_xp(uid, int(tr["xp_reward"]) if chk else -int(tr["xp_reward"]))
                        st.rerun()
                with tc2:
                    if st.button("🗑️", key=f"task_del_{tid}"):
                        conn = DatabaseManager.get_conn()
                        c = conn.cursor()
                        c.execute("DELETE FROM tasks WHERE id = ?", (tid,))
                        conn.commit()
                        conn.close()
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with p_col2:
        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        st.markdown(f"##### 🔁 Ежедневный чек-лист привычек ({today_str})")

        conn = DatabaseManager.get_conn()
        df_hab = pd.read_sql_query("SELECT id, title, category, xp_reward FROM habits WHERE user_id = ?", conn, params=(uid,))
        c = conn.cursor()
        c.execute("SELECT habit_id FROM habit_logs WHERE user_id = ? AND log_date = ? AND status = 1", (uid, today_str))
        done_h_ids = {r[0] for r in c.fetchall()}
        conn.close()

        for _, hr in df_hab.iterrows():
            hid = int(hr["id"])
            h_checked = hid in done_h_ids
            new_h_chk = st.checkbox(
                f"{hr['title']} (`{hr['category']}` • +{hr['xp_reward']} XP)",
                value=h_checked,
                key=f"hab_chk_{hid}_{today_str}"
            )
            if new_h_chk != h_checked:
                conn = DatabaseManager.get_conn()
                c = conn.cursor()
                if new_h_chk:
                    c.execute(
                        "INSERT OR REPLACE INTO habit_logs (user_id, habit_id, log_date, status) VALUES (?, ?, ?, 1)",
                        (uid, hid, today_str)
                    )
                    DatabaseManager.add_xp(uid, int(hr["xp_reward"]))
                else:
                    c.execute(
                        "DELETE FROM habit_logs WHERE user_id = ? AND habit_id = ? AND log_date = ?",
                        (uid, hid, today_str)
                    )
                    DatabaseManager.add_xp(uid, -int(hr["xp_reward"]))
                conn.commit()
                conn.close()
                st.rerun()

        st.markdown("---")
        nh_title = st.text_input("Добавить свою привычку:", placeholder="Например: Растяжка 10 минут", key="hab_new_title")
        if st.button("Сохранить привычку", use_container_width=True, key="hab_add_btn"):
            if nh_title.strip():
                conn = DatabaseManager.get_conn()
                c = conn.cursor()
                c.execute(
                    "INSERT INTO habits (user_id, title, category, xp_reward) VALUES (?, ?, 'Дисциплина', 25)",
                    (uid, nh_title.strip())
                )
                conn.commit()
                conn.close()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# ВКЛАДКА 4: СПОРТ & РЕКОРДЫ
# ------------------------------------------------------------------------------
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
            w_choice = st.selectbox(
                "Выбери направление:",
                list(WORKOUT_PROTOCOLS.keys()),
                key="workout_direction_select_main"
            )
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
                if st.button("🔥 Табата 20/10", use_container_width=True, type="primary", key="timer_tabata_btn_main"):
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
                if st.button("🥋 Раунд (60с)", use_container_width=True, key="timer_round_btn_main"):
                    for s in range(60, 0, -1):
                        tm_display.markdown(f'<div class="breath-box" style="border-color:#d29922;">Раунд: <b>{s} с</b></div>', unsafe_allow_html=True)
                        tm_bar.progress((60 - s) / 60.0)
                        time.sleep(1)
                    tm_display.markdown('<div class="breath-box" style="border-color:#3fb950;">🔔 Гонг!</div>', unsafe_allow_html=True)

            with tc_3:
                if st.button("💧 Отдых (45с)", use_container_width=True, key="timer_rest_btn_main"):
                    for s in range(45, 0, -1):
                        tm_display.markdown(f'<div class="breath-box" style="border-color:{accent_col};">Отдых: <b>{s} с</b></div>', unsafe_allow_html=True)
                        tm_bar.progress((45 - s) / 45.0)
                        time.sleep(1)
                    tm_display.markdown('<div class="breath-box" style="border-color:#3fb950;">⚡ Вперед!</div>', unsafe_allow_html=True)

    with sub_tr2:
        pr_c1, pr_c2 = st.columns([1, 1.3])
        with pr_c1:
            st.markdown('<div class="bento-card">', unsafe_allow_html=True)
            st.markdown("##### Зафиксировать личный максимум")
            pr_cat = st.selectbox(
                "Сфера рекорда:",
                ["Силовая база", "Калистеника", "Единоборства", "Бег / Выносливость", "Учеба и Код"],
                key="pr_cat_select_unique"
            )
            pr_title = st.text_input("Дисциплина:", placeholder="Жим лежа / Подтягивания / Горизонт", key="pr_title_in_unique")
            pr_val = st.number_input("Значение:", min_value=0.0, max_value=50000.0, value=100.0, step=1.0, key="pr_val_in_unique")
            pr_unit = st.text_input("Единицы измерения:", value="кг", key="pr_unit_in_unique")
            pr_dt = st.date_input("Дата рекорда:", value=date.today(), key="pr_dt_in_unique")

            if st.button("🏆 Сохранить PR (+50 XP)", use_container_width=True, type="primary", key="pr_save_btn_unique"):
                if pr_title.strip():
                    conn = DatabaseManager.get_conn()
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO pr_records (user_id, category, record_title, record_value, record_unit, achieved_date) VALUES (?, ?, ?, ?, ?, ?)",
                        (uid, pr_cat, pr_title.strip(), pr_val, pr_unit.strip(), str(pr_dt))
                    )
                    conn.commit()
                    conn.close()
                    DatabaseManager.add_xp(uid, 50)
                    st.success("Рекорд сохранен!")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with pr_c2:
            st.markdown("##### История личных рекордов")
            conn = DatabaseManager.get_conn()
            df_pr = pd.read_sql_query(
                "SELECT category, record_title, record_value, record_unit, achieved_date FROM pr_records WHERE user_id = ? ORDER BY id DESC",
                conn, params=(uid,)
            )
            conn.close()
            if not df_pr.empty:
                for _, r in df_pr.iterrows():
                    st.markdown(f"""
                        <div class="bento-card" style="padding:12px 16px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <div style="font-weight:700;">🏅 {r['record_title']}</div>
                                <div style="font-size:0.78rem; color:#8b949e;">{r['category']} • {r['achieved_date']}</div>
                            </div>
                            <div style="font-size:1.15rem; font-weight:800; color:{accent_col};">
                                {r['record_value']} {r['record_unit']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    with sub_tr3:
        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        st.markdown(f"##### 🥩 Дневной баланс БЖУ и Гидратации ({today_str})")
        conn = DatabaseManager.get_conn()
        c = conn.cursor()
        c.execute("SELECT calories, protein, fats, carbs, water_ml FROM nutrition_logs WHERE user_id = ? AND log_date = ?", (uid, today_str))
        nut_row = c.fetchone()
        conn.close()

        nc1, nc2, nc3, nc4, nc5 = st.columns(5)
        with nc1:
            cal_in = st.number_input("Калории (ккал)", 0, 10000, int(nut_row[0]) if nut_row else 2600, 50, key="nut_cal_in")
        with nc2:
            prot_in = st.number_input("Белки (г)", 0, 500, int(nut_row[1]) if nut_row else 150, 5, key="nut_prot_in")
        with nc3:
            fat_in = st.number_input("Жиры (г)", 0, 500, int(nut_row[2]) if nut_row else 80, 5, key="nut_fat_in")
        with nc4:
            carb_in = st.number_input("Углеводы (г)", 0, 1000, int(nut_row[3]) if nut_row else 300, 10, key="nut_carb_in")
        with nc5:
            wat_in = st.number_input("Вода (мл)", 0, 6000, int(nut_row[4]) if nut_row else 2200, 250, key="nut_wat_in")

        if st.button("Сохранить рацион дня (+15 XP)", type="primary", key="nut_save_btn"):
            conn = DatabaseManager.get_conn()
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO nutrition_logs (user_id, log_date, calories, protein, fats, carbs, water_ml)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (uid, today_str, cal_in, prot_in, fat_in, carb_in, wat_in))
            conn.commit()
            conn.close()
            DatabaseManager.add_xp(uid, 15)
            st.success("Данные по питанию и воде обновлены!")
        st.markdown('</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# ВКЛАДКА 5: БИБЛИОТЕКА (40 КНИГ)
# ------------------------------------------------------------------------------
with tab_lib:
    st.markdown("#### 📚 База Знаний (40 фундаментальных книг) и Конспекты")
    lib_cats = list(LIBRARY_CATALOG.keys())
    picked_lib_cat = st.selectbox("Раздел библиотеки:", lib_cats, key="lib_category_selector")

    books_list = LIBRARY_CATALOG.get(picked_lib_cat, [])
    conn = DatabaseManager.get_conn()
    c = conn.cursor()
    c.execute("SELECT book_title, status, notes, rating FROM book_progress WHERE user_id = ?", (uid,))
    saved_books = {r[0]: (r[1], r[2], r[3]) for r in c.fetchall()}
    conn.close()

    for idx_b, b_item in enumerate(books_list):
        b_title = b_item["title"]
        b_author = b_item["author"]
        b_desc = b_item["desc"]
        def_status = b_item.get("status", "В планах")

        cur_st, cur_note, cur_rat = saved_books.get(b_title, (def_status, "", 5))
        st_color = "#3fb950" if cur_st == "Прочитано" else ("#d29922" if cur_st == "В процессе" else "#8b949e")

        st.markdown(f"""
            <div class="bento-card" style="margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-weight:700; font-size:1.02rem;">📖 {b_title}</span>
                        <span style="color:#8b949e; font-size:0.86rem;"> — {b_author}</span>
                    </div>
                    <span class="pill-badge" style="color:{st_color}; border-color:{st_color};">{cur_st}</span>
                </div>
                <div style="font-size:0.85rem; color:#c9d1d9; margin-top:6px;">{b_desc}</div>
            </div>
        """, unsafe_allow_html=True)

        bc1, bc2, bc3 = st.columns([1, 2, 0.7])
        st_opts = ["В планах", "В процессе", "Прочитано"]
        with bc1:
            new_st = st.selectbox(
                "Статус:",
                st_opts,
                index=st_opts.index(cur_st) if cur_st in st_opts else 0,
                key=f"lib_st_{picked_lib_cat}_{idx_b}"
            )
        with bc2:
            new_nt = st.text_input(
                "Главный инсайт / заметка:",
                value=cur_note,
                placeholder="Что внедряю в жизнь из этой книги...",
                key=f"lib_nt_{picked_lib_cat}_{idx_b}"
            )
        with bc3:
            st.write("")
            if st.button("💾 Сохранить", use_container_width=True, key=f"lib_sv_{picked_lib_cat}_{idx_b}"):
                conn = DatabaseManager.get_conn()
                c = conn.cursor()
                c.execute("""
                    INSERT OR REPLACE INTO book_progress (user_id, book_title, status, notes, rating)
                    VALUES (?, ?, ?, ?, 5)
                """, (uid, b_title, new_st, new_nt.strip()))
                conn.commit()
                conn.close()
                if new_st == "Прочитано" and cur_st != "Прочитано":
                    DatabaseManager.add_xp(uid, 60)
                st.rerun()


# ------------------------------------------------------------------------------
# ВКЛАДКА 6: ЦЕЛИ & 100 ТРОФЕЕВ
# ------------------------------------------------------------------------------
with tab_goals:
    st.markdown("#### 🎯 Стратегические Цели и Зал Славы (100 Трофеев)")
    g_tab1, g_tab2 = st.tabs(["🎯 Управление целями", "🏆 Матрица 100 Трофеев"])

    with g_tab1:
        conn = DatabaseManager.get_conn()
        df_all_g = pd.read_sql_query("SELECT id, title, category, current_val, target_val, unit FROM goals WHERE user_id = ?", conn, params=(uid,))
        conn.close()

        for _, gr in df_all_g.iterrows():
            gid = int(gr["id"])
            gp = min(100, int(round((gr["current_val"] / max(1.0, gr["target_val"])) * 100)))
            st.markdown('<div class="bento-card">', unsafe_allow_html=True)
            st.markdown(f"**{gr['title']}** (`{gr['category']}`) — **{gp}%**")
            st.progress(gp / 100.0)
            gc1, gc2, gc3 = st.columns([1.2, 0.8, 0.5])
            with gc1:
                new_gval = st.number_input(
                    f"Текущий прогресс ({gr['unit']}):",
                    min_value=0.0,
                    max_value=1000000.0,
                    value=float(gr["current_val"]),
                    step=1.0,
                    key=f"goal_val_in_{gid}"
                )
            with gc2:
                st.write("")
                if st.button("Обновить прогресс", use_container_width=True, key=f"goal_upd_btn_{gid}"):
                    conn = DatabaseManager.get_conn()
                    c = conn.cursor()
                    c.execute("UPDATE goals SET current_val = ? WHERE id = ?", (new_gval, gid))
                    conn.commit()
                    conn.close()
                    DatabaseManager.add_xp(uid, 15)
                    st.rerun()
            with gc3:
                st.write("")
                if st.button("Удалить", use_container_width=True, key=f"goal_del_btn_{gid}"):
                    conn = DatabaseManager.get_conn()
                    c = conn.cursor()
                    c.execute("DELETE FROM goals WHERE id = ?", (gid,))
                    conn.commit()
                    conn.close()
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        st.markdown("##### ➕ Поставить новую цель")
        ng_t = st.text_input("Название цели:", placeholder="Например: Собрать портфолио из 20 дизайн-кейсов", key="ng_title_in")
        ng_c1, ng_c2, ng_c3 = st.columns(3)
        with ng_c1:
            ng_cat = st.selectbox("Категория:", ["Спорт", "Интеллект", "Проекты", "Дисциплина"], key="ng_cat_in")
        with ng_c2:
            ng_tar = st.number_input("Целевое число:", min_value=1.0, max_value=1000000.0, value=100.0, key="ng_tar_in")
        with ng_c3:
            ng_un = st.text_input("Единица:", value="кейсов", key="ng_unit_in")

        if st.button("Создать цель", type="primary", key="ng_create_btn"):
            if ng_t.strip():
                conn = DatabaseManager.get_conn()
                c = conn.cursor()
                c.execute(
                    "INSERT INTO goals (user_id, title, category, current_val, target_val, unit) VALUES (?, ?, ?, 0, ?, ?)",
                    (uid, ng_t.strip(), ng_cat, ng_tar, ng_un.strip())
                )
                conn.commit()
                conn.close()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with g_tab2:
        st.caption("Трофеи открываются автоматически по мере роста твоего XP, уровня, закрытых задач и рекордов.")
        t_cols = st.columns(4)
        for t_idx in range(1, 101):
            req_xp = t_idx * 150
            unlocked = user_xp >= req_xp
            col_box = t_cols[(t_idx - 1) % 4]
            with col_box:
                cls_name = "trophy-card trophy-unlocked" if unlocked else "trophy-card"
                icon_t = "🏆" if unlocked else "🔒"
                st.markdown(f"""
                    <div class="{cls_name}">
                        <b>{icon_t} Трофей #{t_idx}</b><br>
                        <span style="color:#8b949e; font-size:0.76rem;">Порог: {req_xp} XP</span>
                    </div>
                """, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# ВКЛАДКА 7: СИСТЕМА, DEEP WORK & БЭКАП
# ------------------------------------------------------------------------------
with tab_sys:
    st.markdown("#### ⚙️ Deep Work Таймер, Дыхательный Резет и Резервное копирование")
    s_col1, s_col2 = st.columns(2)

    with s_col1:
        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        st.markdown("##### 🧘 Таймер Глубокого Фокуса (Deep Work)")
        dw_topic = st.text_input("Над чем работаем сейчас:", value="Подготовка к ЕГЭ / Python / Дизайн", key="dw_topic_in")
        dw_mins = st.selectbox("Длительность сессии (мин):", [15, 25, 45, 60, 90], index=1, key="dw_mins_sel")

        if st.button("🚀 Завершить и засчитать фокус-сессию", type="primary", use_container_width=True, key="dw_finish_btn"):
            earned = int(dw_mins * 2)
            conn = DatabaseManager.get_conn()
            c = conn.cursor()
            c.execute(
                "INSERT INTO focus_sessions (user_id, session_date, minutes, topic, xp_earned) VALUES (?, ?, ?, ?, ?)",
                (uid, today_str, dw_mins, dw_topic.strip(), earned)
            )
            conn.commit()
            conn.close()
            DatabaseManager.add_xp(uid, earned)
            st.success(f"Сессия {dw_mins} мин засчитана! Начислено +{earned} XP.")
            st.rerun()

        st.markdown("---")
        st.markdown("##### 🌬️ Нейро-Резет: Квадратное дыхание (4-4-4-4)")
        br_spot = st.empty()
        if st.button("Запустить 1 цикл дыхания (16 сек)", use_container_width=True, key="sys_breath_btn"):
            phases = [
                ("Вдох носом (4 сек)...", "#58a6ff"),
                ("Задержка дыхания (4 сек)...", "#d29922"),
                ("Плавный выдох (4 сек)...", "#3fb950"),
                ("Пауза на выдохе (4 сек)...", "#a371f7")
            ]
            for ph_text, ph_col in phases:
                for sec in range(4, 0, -1):
                    br_spot.markdown(
                        f'<div class="breath-box" style="border-color:{ph_col};">{ph_text} <b>{sec} с</b></div>',
                        unsafe_allow_html=True
                    )
                    time.sleep(1)
            br_spot.markdown('<div class="breath-box" style="border-color:#3fb950;">✨ Пульс выровнен, фокус восстановлен!</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with s_col2:
        st.markdown('<div class="bento-card">', unsafe_allow_html=True)
        st.markdown("##### 💾 Экспорт и Импорт базы данных (JSON Backup)")
        conn = DatabaseManager.get_conn()
        backup_payload = {
            "exported_at": str(datetime.now()),
            "username": uname,
            "xp": user_xp,
            "tasks": pd.read_sql_query("SELECT * FROM tasks WHERE user_id = ?", conn, params=(uid,)).to_dict(orient="records"),
            "pr_records": pd.read_sql_query("SELECT * FROM pr_records WHERE user_id = ?", conn, params=(uid,)).to_dict(orient="records"),
            "goals": pd.read_sql_query("SELECT * FROM goals WHERE user_id = ?", conn, params=(uid,)).to_dict(orient="records"),
            "bio_logs": pd.read_sql_query("SELECT * FROM bio_logs WHERE user_id = ?", conn, params=(uid,)).to_dict(orient="records")
        }
        conn.close()

        json_str = json.dumps(backup_payload, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Скачать полный JSON-бэкап профиля",
            data=json_str,
            file_name=f"neuroguard_backup_{uname}_{today_str}.json",
            mime="application/json",
            use_container_width=True,
            key="sys_download_backup_btn"
        )

        st.markdown("---")
        st.caption("Статистика текущих записей в хранилище SQLite:")
        st.json({
            "Оператор": uname,
            "Уровень": lvl,
            "Всего XP": user_xp,
            "Задач в базе": len(backup_payload["tasks"]),
            "Личных рекордов (PR)": len(backup_payload["pr_records"]),
            "Активных целей": len(backup_payload["goals"]),
            "Био-замеров": len(backup_payload["bio_logs"])
        })
        st.markdown('</div>', unsafe_allow_html=True)

