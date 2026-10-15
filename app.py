import sqlite3
import time
from datetime import date, datetime
import pandas as pd
import streamlit as st

# --- 1. НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(
    page_title="NeuroGuard SaaS",
    page_icon="⚡",
    layout="wide"
)


# =====================================================================
# МОДУЛЬ 1: DATABASE LAYER (Задачи 1.1 и 1.2 — Реляционная БД с User ID)
# =====================================================================
class DatabaseManager:
    DB_NAME = "neuroguard_saas.db"

    @classmethod
    def get_conn(cls):
        return sqlite3.connect(cls.DB_NAME)

    @classmethod
    def init_db(cls):
        conn = cls.get_conn()
        c = conn.cursor()

        # 1. Таблица пользователей (SaaS / Auth / PRO)
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                pin_code TEXT NOT NULL,
                is_pro INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)

        # 2. Таблица логов здоровья (привязка к user_id)
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_health_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                sleep_hours REAL,
                sleep_quality INTEGER,
                study_hours REAL,
                eye_strain INTEGER,
                training_type TEXT,
                training_intensity INTEGER,
                head_impact INTEGER,
                readiness_score INTEGER,
                ai_advice TEXT,
                UNIQUE(user_id, log_date),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # 3. Таблица RPG-прокачки и планов (привязка к user_id)
        c.execute("""
            CREATE TABLE IF NOT EXISTS rpg_actions_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                exercises_reps INTEGER,
                agility_drills INTEGER,
                book_pages INTEGER,
                topics_learned INTEGER,
                tasks_solved INTEGER,
                plan_text TEXT,
                plan_percent INTEGER,
                total_actions INTEGER,
                xp_earned INTEGER,
                str_pts INTEGER,
                agi_pts INTEGER,
                int_pts INTEGER,
                dsc_pts INTEGER,
                rpg_advice TEXT,
                daily_note TEXT DEFAULT '',
                UNIQUE(user_id, log_date),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # 4. Таблица разблокированных ачивок (привязка к user_id)
        c.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ach_code TEXT NOT NULL,
                unlocked_date TEXT NOT NULL,
                UNIQUE(user_id, ach_code),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # Создаем дефолтный аккаунт основателя, чтобы вход работал мгновенно
        c.execute("SELECT id FROM users WHERE username = 'Igor_Founder'")
        if not c.fetchone():
            c.execute(
                "INSERT INTO users (username, pin_code, is_pro, created_at) VALUES (?, ?, ?, ?)",
                ("Igor_Founder", "0000", 1, str(date.today()))
            )

        conn.commit()
        conn.close()

    @classmethod
    def authenticate_or_register(cls, username: str, pin_code: str, create_new: bool = False):
        conn = cls.get_conn()
        c = conn.cursor()
        username = username.strip()
        if create_new:
            try:
                c.execute(
                    "INSERT INTO users (username, pin_code, is_pro, created_at) VALUES (?, ?, 0, ?)",
                    (username, pin_code, str(date.today()))
                )
                conn.commit()
            except sqlite3.IntegrityError:
                conn.close()
                return None, "Пользователь с таким ником уже существует!"

        c.execute("SELECT id, username, is_pro FROM users WHERE username = ? AND pin_code = ?", (username, pin_code))
        row = c.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "username": row[1], "is_pro": bool(row[2])}, None
        return None, "Неверный никнейм или PIN-код!"

    @classmethod
    def set_pro_status(cls, user_id: int, is_pro: bool):
        conn = cls.get_conn()
        c = conn.cursor()
        c.execute("UPDATE users SET is_pro = ? WHERE id = ?", (int(is_pro), user_id))
        conn.commit()
        conn.close()

    @classmethod
    def save_health_log(cls, data: tuple):
        conn = cls.get_conn()
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO daily_health_logs (
                user_id, log_date, sleep_hours, sleep_quality, study_hours,
                eye_strain, training_type, training_intensity,
                head_impact, readiness_score, ai_advice
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        conn.close()

    @classmethod
    def save_rpg_log(cls, data: tuple):
        conn = cls.get_conn()
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO rpg_actions_logs (
                user_id, log_date, exercises_reps, agility_drills, book_pages,
                topics_learned, tasks_solved, plan_text, plan_percent,
                total_actions, xp_earned, str_pts, agi_pts, int_pts, dsc_pts, rpg_advice, daily_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        conn.close()

    @classmethod
    def load_health_logs(cls, user_id: int) -> pd.DataFrame:
        conn = cls.get_conn()
        df = pd.read_sql_query(
            "SELECT * FROM daily_health_logs WHERE user_id = ? ORDER BY log_date DESC",
            conn, params=(user_id,)
        )
        conn.close()
        return df

    @classmethod
    def load_rpg_logs(cls, user_id: int) -> pd.DataFrame:
        conn = cls.get_conn()
        df = pd.read_sql_query(
            "SELECT * FROM rpg_actions_logs WHERE user_id = ? ORDER BY log_date DESC",
            conn, params=(user_id,)
        )
        conn.close()
        return df

    @classmethod
    def unlock_achievement(cls, user_id: int, ach_code: str):
        conn = cls.get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO achievements (user_id, ach_code, unlocked_date) VALUES (?, ?, ?)",
            (user_id, ach_code, str(date.today()))
        )
        conn.commit()
        conn.close()

    @classmethod
    def get_unlocked_achievements(cls, user_id: int) -> dict:
        conn = cls.get_conn()
        c = conn.cursor()
        c.execute("SELECT ach_code, unlocked_date FROM achievements WHERE user_id = ?", (user_id,))
        rows = c.fetchall()
        conn.close()
        return {r[0]: r[1] for r in rows}


# =====================================================================
# МОДУЛЬ 2: CORE ENGINE (Задачи 2.1, 2.2, 2.3 — Математическое ядро)
# =====================================================================
class CoreEngine:
    @staticmethod
    def calculate_readiness(sleep_h: float, sleep_q: int, study_h: float,
                            eye_strain: int, train_int: int, head_impact: bool) -> int:
        sleep_recovery = min(sleep_h / 8.0, 1.15) * 60 + (sleep_q / 10.0) * 40
        cognitive_penalty = study_h * 2.0
        eye_penalty = max(0, (eye_strain - 1) * 3.8)
        physical_penalty = train_int * 2.2
        impact_penalty = 25 if head_impact else 0
        score = sleep_recovery - (cognitive_penalty + eye_penalty + physical_penalty + impact_penalty)
        return max(0, min(100, int(round(score))))

    @staticmethod
    def calculate_rpg_stats(ex_reps: int, agi_drills: int, pages: int,
                            topics: int, tasks: int, plan_pct: int, is_pro: bool = False):
        str_pts = int(round(ex_reps * 0.4))
        agi_pts = int(round(agi_drills * 3.0 + ex_reps * 0.15))
        int_pts = int(round(pages * 0.8 + topics * 15 + tasks * 5))
        dsc_pts = int(round(plan_pct * 0.5))

        total_actions = ex_reps + agi_drills + pages + topics + tasks
        base_xp = (str_pts + agi_pts + int_pts) * 2
        plan_multiplier = 1.0 + (plan_pct / 200.0)
        pro_multiplier = 1.25 if is_pro else 1.0  # PRO-подписка дает +25% буст к опыту
        xp_earned = int(round(base_xp * plan_multiplier * pro_multiplier))
        return str_pts, agi_pts, int_pts, dsc_pts, total_actions, xp_earned

    @staticmethod
    def get_rank_badge(score_or_pct: int):
        if score_or_pct >= 90:
            return "👑 S-РАНГ", "#f1e05a"
        elif score_or_pct >= 75:
            return "💎 A-РАНГ", "#3fb950"
        elif score_or_pct >= 50:
            return "⚔️ B-РАНГ", "#58a6ff"
        return "🛡️ C-РАНГ", "#d29922"

    @staticmethod
    def evaluate_and_sync_achievements(user_id: int, df_health: pd.DataFrame, df_rpg: pd.DataFrame,
                                       curr_eye: int, curr_impact: bool, curr_plan: int,
                                       curr_reps: int, curr_drills: int, curr_tasks: int,
                                       curr_pages: int, curr_sleep: float, curr_sleep_q: int):
        # Триггеры проверки условий
        triggers = {
            "CRYSTAL_EYE": (curr_eye <= 4 and not curr_impact) or (
                not df_health.empty and ((df_health["eye_strain"] <= 4) & (df_health["head_impact"] == 0)).any()
            ),
            "MONARCH_100": (curr_plan == 100) or (
                not df_rpg.empty and (df_rpg["plan_percent"] == 100).any()
            ),
            "STEEL_100": (curr_reps >= 100) or (
                not df_rpg.empty and (df_rpg["exercises_reps"] >= 100).any()
            ),
            "KOBUDO_MASTER": (curr_drills >= 5) or (
                not df_rpg.empty and (df_rpg["agility_drills"] >= 5).any()
            ),
            "CYBER_ARCH": (curr_tasks >= 10 and curr_pages >= 20) or (
                not df_rpg.empty and ((df_rpg["tasks_solved"] >= 10) & (df_rpg["book_pages"] >= 20)).any()
            ),
            "TITAN_SLEEP": (curr_sleep >= 8.0 and curr_sleep_q >= 8) or (
                not df_health.empty and ((df_health["sleep_hours"] >= 8.0) & (df_health["sleep_quality"] >= 8)).any()
            ),
        }

        for code, is_met in triggers.items():
            if is_met:
                DatabaseManager.unlock_achievement(user_id, code)

        unlocked_map = DatabaseManager.get_unlocked_achievements(user_id)

        catalog = [
            {"code": "CRYSTAL_EYE", "icon": "👁️", "title": "Кристальный Взгляд", "desc": "Удержать усталость глаз ≤ 4 без ударной нагрузки"},
            {"code": "MONARCH_100", "icon": "👑", "title": "Абсолютный Монарх", "desc": "Закрыть все квесты плана дня на 100%"},
            {"code": "STEEL_100", "icon": "🦾", "title": "Сотка Стали", "desc": "Выполнить 100+ силовых повторений за один день"},
            {"code": "KOBUDO_MASTER", "icon": "🥋", "title": "Мастер Кобудо", "desc": "Отработать 5+ раундов техники в воздух / с оружием"},
            {"code": "CYBER_ARCH", "icon": "🧠", "title": "Кибер-Архитектор", "desc": "Решить 10+ задач и прочитать 20+ страниц за день"},
            {"code": "TITAN_SLEEP", "icon": "💤", "title": "Титановая Регенерация", "desc": "Проспать 8+ часов с качеством сна ≥ 8/10"}
        ]

        for item in catalog:
            code = item["code"]
            item["unlocked"] = code in unlocked_map
            item["date"] = unlocked_map.get(code, "")
        return catalog

    @staticmethod
    def generate_weekly_report(username: str, is_pro: bool, df_health: pd.DataFrame, df_rpg: pd.DataFrame) -> str:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        tier = "PRO-Аккаунт 💎" if is_pro else "Базовый (Free)"
        lines = [
            "==========================================",
            "⚡ NEUROGUARD: ОФИЦИАЛЬНАЯ СВОДКА МОНИТОРИНГА",
            f"👤 Пользователь: {username} ({tier})",
            f"📅 Дата формирования: {now_str}",
            "==========================================\n",
            "1. МЕДИЦИНСКИЙ И БИО-ПРОФИЛЬ (ЗРЕНИЕ И ЦНС):"
        ]
        if not df_health.empty:
            h7 = df_health.head(7)
            lines.append(f"• Записей проанализировано: {len(h7)} дн.")
            lines.append(f"• Средняя продолжительность сна: {h7['sleep_hours'].mean():.1f} ч (качество: {h7['sleep_quality'].mean():.1f}/10)")
            lines.append(f"• Среднее экранное время (учеба/код): {h7['study_hours'].mean():.1f} ч/день")
            lines.append(f"• Индекс зрительного утомления (спазм): {h7['eye_strain'].mean():.1f} / 10 (Пик: {h7['eye_strain'].max()}/10)")
            lines.append(f"• Средний индекс готовности ЦНС (Readiness): {h7['readiness_score'].mean():.0f}%")
            impacts = int(h7['head_impact'].sum())
            lines.append(f"• Эпизоды ударной нагрузки / натуживания: {impacts} дн.")
            if h7['eye_strain'].mean() >= 5.5 or impacts > 0:
                lines.append("⚠️ РЕКОМЕНДАЦИЯ ВРАЧУ/ТРЕНЕРУ: Зафиксирована повышенная нагрузка на сетчатку. Показан бесконтактный режим тренировок и гигиена зрения 20-20-20.")
            else:
                lines.append("✅ СТАТУС ЗРЕНИЯ: Показатели спазма аккомодации в пределах безопасной нормы.")
        else:
            lines.append("• Нет сохраненных био-записей за период.")

        lines.append("\n2. ДИСЦИПЛИНА И ПРОДУКТИВНОСТЬ (RPG-МОДУЛЬ):")
        if not df_rpg.empty:
            r7 = df_rpg.head(7)
            total_xp = int(df_rpg['xp_earned'].sum())
            lvl = (total_xp // 500) + 1
            lines.append(f"• Текущий уровень игрока: LVL {lvl} ({total_xp} XP)")
            lines.append(f"• Среднее выполнение дневного плана: {r7['plan_percent'].mean():.0f}%")
            lines.append(f"• Выполнено упражнений (ОФП): {int(r7['exercises_reps'].sum())} повт.")
            lines.append(f"• Отработано раундов техники / кобудо: {int(r7['agility_drills'].sum())}")
            lines.append(f"• Решено задач (ЕГЭ / Код): {int(r7['tasks_solved'].sum())} шт.")
            lines.append(f"• Прочитано страниц профильной литературы: {int(r7['book_pages'].sum())} стр.")
        else:
            lines.append("• Нет сохраненных записей продуктивности за период.")

        lines.append("\n==========================================")
        lines.append("Сгенерировано автоматически системой NeuroGuard SaaS.")
        return "\n".join(lines)


# Инициализация БД и сессии пользователя
DatabaseManager.init_db()
if "current_user" not in st.session_state:
    st.session_state.current_user = {"id": 1, "username": "Igor_Founder", "is_pro": True}


# =====================================================================
# МОДУЛЬ 3: САЙДБАР — АВТОРИЗАЦИЯ И MОНЕТИЗАЦИЯ (Задачи 4.1 и 4.2)
# =====================================================================
with st.sidebar:
    st.header("🔐 Аккаунт (SaaS Auth)")
    cur_u = st.session_state.current_user
    pro_badge = "💎 PRO" if cur_u["is_pro"] else "🆓 FREE"
    st.markdown(f"Вы вошли как: **`{cur_u['username']}`** ({pro_badge})")

    with st.expander("🔄 Сменить / Создать профиль"):
        auth_mode = st.radio("Режим:", ["Вход в аккаунт", "Регистрация нового"], horizontal=True)
        inp_user = st.text_input("Никнейм", value=cur_u["username"])
        inp_pin = st.text_input("PIN-код (4 цифры)", value="0000", type="password", max_chars=8)
        if st.button("🚀 Применить", use_container_width=True):
            user_obj, err = DatabaseManager.authenticate_or_register(
                inp_user, inp_pin, create_new=(auth_mode == "Регистрация нового")
            )
            if err:
                st.error(err)
            else:
                st.session_state.current_user = user_obj
                st.success(f"Профиль {user_obj['username']} активен!")
                st.rerun()

    st.divider()
    st.header("💎 Подписка NeuroGuard PRO")
    is_pro_toggle = st.toggle(
        "Активировать PRO-режим",
        value=cur_u["is_pro"],
        help="Дает +25% буст к XP, золотой статус и разблокирует скачивание отчетов для врача/тренера."
    )
    if is_pro_toggle != cur_u["is_pro"]:
        DatabaseManager.set_pro_status(cur_u["id"], is_pro_toggle)
        st.session_state.current_user["is_pro"] = is_pro_toggle
        st.rerun()

    if is_pro_toggle:
        st.caption("✅ **PRO активен:** Буст +25% XP, экспорт отчетов `.txt` и премиум-аналитика включены.")
    else:
        st.caption("🔒 **FREE-версия:** Включи PRO выше, чтобы получить +25% к опыту и экспорт медицинских сводок.")

    st.divider()
    dark_mode = st.toggle("🌙 Eye-Safe Mode (Тёмная тема)", value=True)

# Загружаем персональные данные текущего пользователя из БД
uid = st.session_state.current_user["id"]
 uname = st.session_state.current_user["username"]
is_pro = st.session_state.current_user["is_pro"]

df_logs = DatabaseManager.load_health_logs(uid)
df_rpg = DatabaseManager.load_rpg_logs(uid)


# =====================================================================
# МОДУЛЬ 4: MOBILE HUD CSS (Задача 3.1)
# =====================================================================
bg_main = "#0d1117" if dark_mode else "#ffffff"
bg_card = "#161b22" if dark_mode else "#f6f8fa"
border_col = "#30363d" if dark_mode else "#d0d7de"
text_col = "#e6edf3" if dark_mode else "#1f2328"

st.markdown(f"""
    <style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: {bg_main} !important;
        color: {text_col} !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: {bg_card} !important;
        border-right: 1px solid {border_col} !important;
    }}
    h1, h2, h3, h4, p, span, label, .stMarkdown, [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
        color: {text_col} !important;
    }}
    div[data-baseweb="select"] > div, input, textarea {{
        background-color: {bg_card} !important;
        color: {text_col} !important;
        border: 1px solid {border_col} !important;
    }}
    .hud-row {{
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin-bottom: 10px;
    }}
    .hud-pill {{
        background-color: {bg_card};
        border: 1px solid {border_col};
        border-radius: 18px;
        padding: 5px 12px;
        font-size: 13px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }}
    .pro-pill {{
        border: 1px solid #f1e05a !important;
        background: linear-gradient(135deg, rgba(241,224,90,0.18), rgba(22,27,34,0.9));
        color: #f1e05a !important;
    }}
    .stat-mini-card {{
        background-color: {bg_card};
        border: 1px solid {border_col};
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .ach-card {{
        background-color: {bg_card};
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 10px;
        border: 1px solid {border_col};
    }}
    .ach-unlocked {{
        border: 1px solid #3fb950 !important;
        background: linear-gradient(135deg, rgba(63,185,80,0.14), rgba(22,27,34,0.9));
    }}
    .ach-locked {{
        opacity: 0.45;
    }}
    .breath-box {{
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        font-size: 20px;
        font-weight: 700;
        margin: 10px 0;
        border: 2px solid #58a6ff;
        background: rgba(88, 166, 255, 0.12);
    }}
    </style>
""", unsafe_allow_html=True)

# --- ВЕРХНИЙ HUD-БАР ПЕРСОНАЖА ---
hist_xp = int(df_rpg["xp_earned"].sum()) if not df_rpg.empty else 0
player_lvl = (hist_xp // 500) + 1
last_readiness = int(df_logs.iloc[0]["readiness_score"]) if not df_logs.empty else 75
rank_txt, rank_col = CoreEngine.get_rank_badge(last_readiness)
tier_pill = '<span class="hud-pill pro-pill">💎 PRO x1.25 XP</span>' if is_pro else '<span class="hud-pill">🆓 FREE</span>'

st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; margin-bottom:6px;">
    <h3 style="margin:0;">⚡ {uname}</h3>
    <div class="hud-row" style="margin:0;">
        {tier_pill}
        <span class="hud-pill" style="border-color:{rank_col}; color:{rank_col};">{rank_txt}</span>
        <span class="hud-pill">🏅 LVL {player_lvl}</span>
        <span class="hud-pill">✨ {hist_xp} XP</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 5 компактных вкладок со значками
tab_bio, tab_rpg, tab_ach, tab_sos, tab_rep = st.tabs([
    "🛡️ БИО",
    "⚔️ СТАТЫ",
    "🏆 ТРОФЕИ",
    "🧘 РЕЗЕТ",
    "📄 ОТЧЕТ"
])


# =====================================================================
# ВКЛАДКА 1: 🛡️ БИО (ЗДОРОВЬЕ, СЕТЧАТКА И ЦНС)
# =====================================================================
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
        st.markdown("#### 📡 Индекс готовности")
        current_score = CoreEngine.calculate_readiness(
            sleep_hours, sleep_quality, study_hours, eye_strain, training_intensity, head_impact
        )

        b_rank, b_col = CoreEngine.get_rank_badge(current_score)
        eye_badge = "🟢 Глаза ОК" if eye_strain <= 4 else ("🟡 Внимание" if eye_strain <= 6 else "🔴 ОПАСНОСТЬ")
        cns_badge = "🟢 ЦНС В ТОНУСЕ" if current_score >= 65 else ("🟡 УТОМЛЕНИЕ" if current_score >= 45 else "🔴 ПЕРЕГРУЗ")

        st.markdown(f"""
        <div class="hud-row">
            <span class="hud-pill" style="border-color:{b_col};">{b_rank}</span>
            <span class="hud-pill">{eye_badge}</span>
            <span class="hud-pill">{cns_badge}</span>
        </div>
        """, unsafe_allow_html=True)

        score_delta = None
        if not df_logs.empty:
            last_s = int(df_logs.iloc[0]["readiness_score"])
            score_delta = f"{current_score - last_s}%"

        st.metric(label="🔋 Заряд организма (Readiness)", value=f"{current_score}%", delta=score_delta)
        st.progress(current_score / 100)

        advice_parts = []
        if eye_strain >= 6 or head_impact:
            advice_parts.append("🛑 **ОФТАЛЬМО-БЛОК:** Исключи спарринги, натуживания и сократи экран. Выполни протокол во вкладке **🧘 РЕЗЕТ**.")
        else:
            advice_parts.append("👁️ **ЗРЕНИЕ:** В норме. Соблюдай правило 20-20-20 при написании кода и подготовке к ЕГЭ.")

        if current_score < 50:
            advice_parts.append("💤 **ЦНС:** Ресурс снижен. Сегодня только легкая разминка и 8+ часов сна.")
        else:
            advice_parts.append("⚡ **РЕЖИМ:** Отличный тонус для учебы, турников и отработки техники.")

        advice = "\n\n".join(advice_parts)
        st.info(advice)

        if analyze_btn:
            DatabaseManager.save_health_log((
                uid, str(log_date), sleep_hours, sleep_quality, study_hours,
                eye_strain, training_type, training_intensity,
                int(head_impact), current_score, advice
            ))
            df_logs = DatabaseManager.load_health_logs(uid)
            st.success("✅ Био-статус сохранен в твой профиль!")

    if not df_logs.empty:
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("💤 Ср. сон", f"{df_logs['sleep_hours'].mean():.1f} ч")
        m2.metric("👁️ Ср. спазм", f"{df_logs['eye_strain'].mean():.1f}/10")
        m3.metric("🔋 Ср. заряд", f"{df_logs['readiness_score'].mean():.0f}%")

        chart_df = df_logs[["log_date", "readiness_score", "eye_strain", "sleep_hours"]].sort_values("log_date")
        st.line_chart(chart_df.set_index("log_date"))


# =====================================================================
# ВКЛАДКА 2: ⚔️ СТАТЫ (RPG-ПРОКАЧКА, ПЛАН И ДНЕВНИК ВОИНА)
# =====================================================================
with tab_rpg:
    rpg_col1, rpg_col2 = st.columns([1.1, 1])

    with rpg_col1:
        st.markdown("#### 🎯 Квесты на день")
        rpg_date = st.date_input("📅 Дата", value=date.today(), key="rpg_date")

        default_plan = "100 подтягиваний\n5 задач (ЕГЭ / Python)\n15 страниц книги\n3 раунда техники / кобудо"
        plan_text = st.text_area("Список задач (каждая с новой строки):", value=default_plan, height=100)

        tasks_list = [t.strip() for t in plan_text.split("\n") if t.strip()]
        if tasks_list:
            completed_tasks = 0
            for idx, task_item in enumerate(tasks_list):
                if st.checkbox(f"✅ {task_item}", key=f"task_chk_{idx}"):
                    completed_tasks += 1
            plan_percent = int(round((completed_tasks / len(tasks_list)) * 100))
        else:
            plan_percent = st.slider("Выполнение (%)", 0, 100, 70)

        st.markdown("#### 🔢 Выполненный объем")
        rc1, rc2 = st.columns(2)
        with rc1:
            exercises_reps = st.number_input("💪 Повторения (ОФП)", 0, 2000, 100, 10)
            agility_drills = st.number_input("⚡ Раунды техники", 0, 50, 3, 1)
            book_pages = st.number_input("📖 Страницы книг", 0, 500, 15, 5)
        with rc2:
            topics_learned = st.number_input("🧠 Пройдено тем", 0, 20, 1, 1)
            tasks_solved = st.number_input("💻 Решено задач", 0, 200, 5, 1)

        daily_note = st.text_input("📓 Заметка воина (итог дня):", placeholder="Например: Сделал сотку на турнике, разобрал 2 задачи")
        save_rpg_btn = st.button("⚔️ Зафиксировать статы и дневник", use_container_width=True, type="primary")

    with rpg_col2:
        st.markdown("#### 🧬 Характеристики Персонажа")

        str_pts, agi_pts, int_pts, dsc_pts, total_actions, xp_earned = CoreEngine.calculate_rpg_stats(
            exercises_reps, agility_drills, book_pages, topics_learned, tasks_solved, plan_percent, is_pro=is_pro
        )

        hist_str = int(df_rpg["str_pts"].sum()) if not df_rpg.empty else 0
        hist_agi = int(df_rpg["agi_pts"].sum()) if not df_rpg.empty else 0
        hist_int = int(df_rpg["int_pts"].sum()) if not df_rpg.empty else 0
        hist_dsc = int(df_rpg["dsc_pts"].sum()) if not df_rpg.empty else 0

        total_xp = hist_xp + xp_earned
        lvl_now = (total_xp // 500) + 1
        xp_mod = total_xp % 500
        p_rank, p_col = CoreEngine.get_rank_badge(plan_percent)

        st.markdown(f"""
        <div class="hud-row">
            <span class="hud-pill" style="border-color:{p_col};">{p_rank}</span>
            <span class="hud-pill">🎯 План: {plan_percent}%</span>
            <span class="hud-pill">🔥 Действий: {total_actions}</span>
            <span class="hud-pill">✨ +{xp_earned} XP</span>
        </div>
        """, unsafe_allow_html=True)

        st.progress(xp_mod / 500.0, text=f"🏅 LVL {lvl_now}  •  {xp_mod} / 500 XP до след. уровня")

        st.markdown(f"""
        <div class="stat-mini-card">
            <span>💪 <b>STR</b> (Сила)</span>
            <span><b>{hist_str + str_pts}</b> <span style="color:#3fb950;">(+{str_pts})</span></span>
        </div>
        <div class="stat-mini-card">
            <span>⚡ <b>AGI</b> (Ловкость)</span>
            <span><b>{hist_agi + agi_pts}</b> <span style="color:#3fb950;">(+{agi_pts})</span></span>
        </div>
        <div class="stat-mini-card">
            <span>🧠 <b>INT</b> (Интеллект)</span>
            <span><b>{hist_int + int_pts}</b> <span style="color:#3fb950;">(+{int_pts})</span></span>
        </div>
        <div class="stat-mini-card">
            <span>🛡️ <b>DSC</b> (Дисциплина)</span>
            <span><b>{hist_dsc + dsc_pts}</b> <span style="color:#3fb950;">(+{dsc_pts})</span></span>
        </div>
        """, unsafe_allow_html=True)

        if plan_percent < 50:
            rpg_advice_text = "📉 **Тактика:** Дроби квесты на короткие спринты по 20 минут. Закрывай главный квест до обеда."
        elif plan_percent < 85:
            rpg_advice_text = "📈 **Тактика:** Чтобы дожать 100%, используй таймер 25/5 без телефона."
        else:
            rpg_advice_text = "👑 **Тактика:** S-Ранг! Максимальный множитель опыта активен."

        st.info(rpg_advice_text)

        if save_rpg_btn:
            DatabaseManager.save_rpg_log((
                uid, str(rpg_date), exercises_reps, agility_drills, book_pages,
                topics_learned, tasks_solved, plan_text, plan_percent,
                total_actions, xp_earned, str_pts, agi_pts, int_pts, dsc_pts, rpg_advice_text, daily_note
            ))
            df_rpg = DatabaseManager.load_rpg_logs(uid)
            st.success("✅ Статы, опыт и заметка сохранены в БД!")

    if not df_rpg.empty:
        st.divider()
        st.markdown("#### 📓 Лента Дневника и Тренд Продуктивности")
        notes_df = df_rpg[df_rpg["daily_note"].fillna("") != ""]
        for _, row in notes_df.head(5).iterrows():
            st.markdown(f"""
            <div class="stat-mini-card">
                <span>📅 <b>{row['log_date']}</b>: {row['daily_note']}</span>
                <span class="hud-pill">🎯 {row['plan_percent']}% | +{row['xp_earned']} XP</span>
            </div>
            """, unsafe_allow_html=True)
        rpg_chart = df_rpg[["log_date", "plan_percent", "xp_earned"]].sort_values("log_date")
        st.line_chart(rpg_chart.set_index("log_date"))


# =====================================================================
# ВКЛАДКА 3: 🏆 ТРОФЕИ (АВТО-СОХРАНЕНИЕ В ТАБЛИЦУ ACHIEVEMENTS — Задача 2.2)
# =====================================================================
with tab_ach:
    st.markdown("#### 🏆 Зал Трофеев (База Достижений)")
    st.caption("При выполнении условия трофей автоматически разблокируется и навсегда фиксируется в базе за твоим User ID.")

    ach_catalog = CoreEngine.evaluate_and_sync_achievements(
        uid, df_logs, df_rpg,
        eye_strain, head_impact, plan_percent,
        exercises_reps, agility_drills, tasks_solved,
        book_pages, sleep_hours, sleep_quality
    )

    unlocked_count = sum(1 for a in ach_catalog if a["unlocked"])
    st.progress(unlocked_count / len(ach_catalog), text=f"Разблокировано трофеев: {unlocked_count} из {len(ach_catalog)}")

    ac1, ac2 = st.columns(2)
    for i, ach in enumerate(ach_catalog):
        target_col = ac1 if i % 2 == 0 else ac2
        css_cls = "ach-card ach-unlocked" if ach["unlocked"] else "ach-card ach-locked"
        status_ico = f"✅ {ach['date']}" if ach["unlocked"] else "🔒 ЗАКРЫТО"
        with target_col:
            st.markdown(f"""
            <div class="{css_cls}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:19px; font-weight:700;">{ach['icon']} {ach['title']}</span>
                    <span class="hud-pill">{status_ico}</span>
                </div>
                <p style="margin:6px 0 0 0; font-size:13px;">{ach['desc']}</p>
            </div>
            """, unsafe_allow_html=True)


# =====================================================================
# ВКЛАДКА 4: 🧘 РЕЗЕТ (АНИМАЦИЯ ДЫХАНИЯ 4-7-8 + ТАЙМЕР — Задача 3.2)
# =====================================================================
with tab_sos:
    st.markdown("#### 🧘 Нейро-Резет: Разгрузка сетчатки и ЦНС")
    sos_c1, sos_c2 = st.columns(2)

    with sos_c1:
        st.markdown("##### 👁️ Таймер Пальминга (60 сек)")
        st.caption("Разотри ладони до тепла, прикрой закрытые глаза без давления и запусти таймер.")
        if st.button("▶️ Запустить 60 сек Пальминга", use_container_width=True, type="primary"):
            bar = st.progress(0, text="Закрой глаза... Расслабь цилиарную мышцу...")
            status_box = st.empty()
            for sec in range(1, 61):
                phase_color = "#58a6ff" if sec < 30 else ("#d29922" if sec < 50 else "#3fb950")
                status_box.markdown(
                    f'<div class="breath-box" style="border-color:{phase_color};">'
                    f'👁️ Восстановление сетчатки: <b>{60 - sec} сек</b> осталось</div>',
                    unsafe_allow_html=True
                )
                bar.progress(sec / 60.0)
                time.sleep(1)
            status_box.markdown(
                '<div class="breath-box" style="border-color:#3fb950; background:rgba(63,185,80,0.2);">'
                '✅ Пальминг завершен! Спазм аккомодации снят.</div>',
                unsafe_allow_html=True
            )
            st.balloons()

    with sos_c2:
        st.markdown("##### 🌬️ Интерактивный тренажер дыхания 4-7-8")
        st.caption("Снижает пульс, кортизол и внутриглазное напряжение за 1 цикл (19 сек).")
        if st.button("🌬️ Запустить цикл дыхания 4-7-8", use_container_width=True):
            breath_placeholder = st.empty()
            b_bar = st.progress(0)
            phases = [
                ("🟢 ВДОХ НОСОМ (4 сек)", 4, "#3fb950"),
                ("🟡 ЗАДЕРЖКА ДЫХАНИЯ (7 сек)", 7, "#d29922"),
                ("🔵 МЕДЛЕННЫЙ ВЫДОХ РТОМ (8 сек)", 8, "#58a6ff")
            ]
            total_sec = 19
            elapsed = 0
            for label, duration, col in phases:
                for s in range(duration, 0, -1):
                    elapsed += 1
                    breath_placeholder.markdown(
                        f'<div class="breath-box" style="border-color:{col};">'
                        f'{label}<br><span style="font-size:28px;">{s} с</span></div>',
                        unsafe_allow_html=True
                    )
                    b_bar.progress(elapsed / total_sec)
                    time.sleep(1)
            breath_placeholder.markdown(
                '<div class="breath-box" style="border-color:#3fb950;">'
                '✨ Цикл завершен! Парасимпатическая система активирована.</div>',
                unsafe_allow_html=True
            )


# =====================================================================
# ВКЛАДКА 5: 📄 ОТЧЕТ (ГЕНЕРАЦИЯ И ЭКСПОРТ СВОДКИ — Задача 2.3 и 4.2)
# =====================================================================
with tab_rep:
    st.markdown("#### 📄 Генератор отчета (Для врача-офтальмолога / тренера / защиты)")
    report_text = CoreEngine.generate_weekly_report(uname, is_pro, df_logs, df_rpg)

    st.text_area("Предпросмотр официальной сводки за неделю:", value=report_text, height=280)

    if is_pro:
        st.download_button(
            label="📥 Скачать отчет файлом (.TXT)",
            data=report_text.encode("utf-8"),
            file_name=f"NeuroGuard_Report_{uname}_{date.today()}.txt",
            mime="text/plain",
            use_container_width=True,
            type="primary"
        )
    else:
        st.warning("🔒 Скачивание файла отчета доступно в версии **💎 PRO**. Включи переключатель PRO в боковой панели слева!")
