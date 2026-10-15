import sqlite3
import time
from datetime import date
import pandas as pd
import streamlit as st

# --- 1. НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(
    page_title="NeuroGuard HUD",
    page_icon="⚡",
    layout="wide"
)

# --- 2. БАЗА ДАННЫХ SQLITE (С АВТО-ОБНОВЛЕНИЕМ КОЛОНОК) ---
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS rpg_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT UNIQUE,
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
            daily_note TEXT DEFAULT ''
        )
    """)
    # Безопасное добавление колонки заметки, если таблица уже была создана ранее
    try:
        c.execute("ALTER TABLE rpg_logs ADD COLUMN daily_note TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
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

def save_rpg_log(data):
    conn = sqlite3.connect("recovery_tracker.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO rpg_logs (
            log_date, exercises_reps, agility_drills, book_pages,
            topics_learned, tasks_solved, plan_text, plan_percent,
            total_actions, xp_earned, str_pts, agi_pts, int_pts, dsc_pts, rpg_advice, daily_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

def load_logs():
    conn = sqlite3.connect("recovery_tracker.db")
    df = pd.read_sql_query("SELECT * FROM daily_logs ORDER BY log_date DESC", conn)
    conn.close()
    return df

def load_rpg_logs():
    conn = sqlite3.connect("recovery_tracker.db")
    df = pd.read_sql_query("SELECT * FROM rpg_logs ORDER BY log_date DESC", conn)
    conn.close()
    return df

# --- 3. МАТЕМАТИЧЕСКИЕ МОДЕЛИ ---
def calculate_readiness(sleep_h, sleep_q, study_h, eye_strain, train_int, head_impact):
    sleep_recovery = min(sleep_h / 8.0, 1.15) * 60 + (sleep_q / 10.0) * 40
    cognitive_penalty = study_h * 2.0
    eye_penalty = max(0, (eye_strain - 1) * 3.8)
    physical_penalty = train_int * 2.2
    impact_penalty = 25 if head_impact else 0
    score = sleep_recovery - (cognitive_penalty + eye_penalty + physical_penalty + impact_penalty)
    return max(0, min(100, int(round(score))))

def calculate_rpg_stats(ex_reps, agi_drills, pages, topics, tasks, plan_pct):
    str_pts = int(round(ex_reps * 0.4))
    agi_pts = int(round(agi_drills * 3.0 + ex_reps * 0.15))
    int_pts = int(round(pages * 0.8 + topics * 15 + tasks * 5))
    dsc_pts = int(round(plan_pct * 0.5))
    total_actions = ex_reps + agi_drills + pages + topics + tasks
    base_xp = (str_pts + agi_pts + int_pts) * 2
    multiplier = 1.0 + (plan_pct / 200.0)
    xp_earned = int(round(base_xp * multiplier))
    return str_pts, agi_pts, int_pts, dsc_pts, total_actions, xp_earned

def get_rank_badge(score_or_pct):
    if score_or_pct >= 90:
        return "👑 S-РАНГ", "#f1e05a"
    elif score_or_pct >= 75:
        return "💎 A-РАНГ", "#3fb950"
    elif score_or_pct >= 50:
        return "⚔️ B-РАНГ", "#58a6ff"
    else:
        return "🛡️ C-РАНГ", "#d29922"

init_db()
df_logs = load_logs()
df_rpg = load_rpg_logs()

# --- 4. САЙДБАР И СТИЛИ ЗНАЧКОВ (HUD DARK MODE) ---
with st.sidebar:
    st.header("⚙️ HUD-Панель")
    dark_mode = st.toggle("🌙 Eye-Safe Mode", value=True)
    st.divider()
    st.markdown(
        "**Профиль:**\n"
        "* 🎓 `10 класс | ЕГЭ | Python`\n"
        "* 🥋 `Каратэ | Кобудо | ОФП`\n"
        "* 👁️ `Защита сетчатки и ЦНС`"
    )

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
    /* Компактные HUD-бейджи и карточки */
    .hud-row {{
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }}
    .hud-pill {{
        background-color: {bg_card};
        border: 1px solid {border_col};
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 14px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
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
        background: linear-gradient(135deg, rgba(63,185,80,0.12), rgba(22,27,34,0.9));
    }}
    .ach-locked {{
        opacity: 0.5;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 5. ВЕРХНЯЯ ШАПКА СО ЗНАЧКАМИ ---
hist_xp = int(df_rpg["xp_earned"].sum()) if not df_rpg.empty else 0
player_lvl = (hist_xp // 500) + 1
last_readiness = int(df_logs.iloc[0]["readiness_score"]) if not df_logs.empty else 75
rank_txt, rank_col = get_rank_badge(last_readiness)

st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; margin-bottom:5px;">
    <h2 style="margin:0;">⚡ NEUROGUARD</h2>
    <div class="hud-row" style="margin:0;">
        <span class="hud-pill" style="border-color:{rank_col}; color:{rank_col};">{rank_txt}</span>
        <span class="hud-pill">🏅 LVL {player_lvl}</span>
        <span class="hud-pill">✨ {hist_xp} XP</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 4 компактные вкладки-значка (идеально помещаются на экране смартфона)
tab_bio, tab_rpg, tab_ach, tab_sos = st.tabs([
    "🛡️ БИО",
    "⚔️ СТАТЫ",
    "🏆 ТРОФЕИ",
    "🧘 РЕЗЕТ"
])

# =====================================================================
# ВКЛАДКА 1: 🛡️ БИО (ЗДОРОВЬЕ И ЗРЕНИЕ)
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
        current_score = calculate_readiness(
            sleep_hours, sleep_quality, study_hours, eye_strain, training_intensity, head_impact
        )
        
        b_rank, b_col = get_rank_badge(current_score)
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

        st.metric(label="🔋 Заряд организма", value=f"{current_score}%", delta=score_delta)
        st.progress(current_score / 100)

        advice_parts = []
        if eye_strain >= 6 or head_impact:
            advice_parts.append("🛑 **ОФТАЛЬМО-БЛОК:** Исключи спарринги, тяжелые веса и сократи экран. Перейди во вкладку **🧘 РЕЗЕТ**.")
        else:
            advice_parts.append("👁️ **ЗРЕНИЕ:** Норма. Держи тайминг 20-20-20 при кодинге и подготовке.")
        
        if current_score < 50:
            advice_parts.append("💤 **ЦНС:** Ресурс просел. Сегодня только легкая разминка и 8+ часов сна.")
        else:
            advice_parts.append("⚡ **РЕЖИМ:** Отличный тонус для учебы, турников и отработки техники.")
        
        advice = "\n\n".join(advice_parts)
        st.info(advice)

        if analyze_btn:
            save_log((
                str(log_date), sleep_hours, sleep_quality, study_hours,
                eye_strain, training_type, training_intensity,
                int(head_impact), current_score, advice
            ))
            df_logs = load_logs()
            st.success("✅ Био-статус записан в базу!")

    if not df_logs.empty:
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("💤 Ср. сон", f"{df_logs['sleep_hours'].mean():.1f} ч")
        m2.metric("👁️ Ср. спазм", f"{df_logs['eye_strain'].mean():.1f}/10")
        m3.metric("🔋 Ср. заряд", f"{df_logs['readiness_score'].mean():.0f}%")
        
        chart_df = df_logs[["log_date", "readiness_score", "eye_strain", "sleep_hours"]].sort_values("log_date")
        st.line_chart(chart_df.set_index("log_date"))


# =====================================================================
# ВКЛАДКА 2: ⚔️ СТАТЫ (ПРОКАЧКА, ПЛАН И ДНЕВНИК ВОИНА)
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

        daily_note = st.text_input("📓 Заметка воина (короткий итог дня):", placeholder="Например: Сделал лесенку на турнике, разобрал 15-е задание ЕГЭ")
        save_rpg_btn = st.button("⚔️ Зафиксировать статы и дневник", use_container_width=True, type="primary")

    with rpg_col2:
        st.markdown("#### 🧬 Характеристики")

        str_pts, agi_pts, int_pts, dsc_pts, total_actions, xp_earned = calculate_rpg_stats(
            exercises_reps, agility_drills, book_pages, topics_learned, tasks_solved, plan_percent
        )

        hist_str = int(df_rpg["str_pts"].sum()) if not df_rpg.empty else 0
        hist_agi = int(df_rpg["agi_pts"].sum()) if not df_rpg.empty else 0
        hist_int = int(df_rpg["int_pts"].sum()) if not df_rpg.empty else 0
        hist_dsc = int(df_rpg["dsc_pts"].sum()) if not df_rpg.empty else 0

        total_xp = hist_xp + xp_earned
        lvl_now = (total_xp // 500) + 1
        xp_mod = total_xp % 500
        p_rank, p_col = get_rank_badge(plan_percent)

        # Компактные значки вместо длинного текста
        st.markdown(f"""
        <div class="hud-row">
            <span class="hud-pill" style="border-color:{p_col};">{p_rank}</span>
            <span class="hud-pill">🎯 План: {plan_percent}%</span>
            <span class="hud-pill">🔥 Действий: {total_actions}</span>
            <span class="hud-pill">✨ +{xp_earned} XP</span>
        </div>
        """, unsafe_allow_html=True)

        st.progress(xp_mod / 500.0, text=f"🏅 LVL {lvl_now}  •  {xp_mod} / 500 XP")

        # 4 мини-карточки характеристик со значками
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

        # Тактический совет
        if plan_percent < 50:
            rpg_advice_text = "📉 **Тактика:** Дроби квесты на мелкие шаги по 20 минут. Закрывай главный квест с утра."
        elif plan_percent < 85:
            rpg_advice_text = "📈 **Тактика:** Чтобы дожать 100%, включай фокус-блоки 25/5 без уведомлений."
        else:
            rpg_advice_text = "👑 **Тактика:** S-Ранг! Максимальный буст опыта (+50% XP). Завтра можно поднять планку на +10%."

        st.info(rpg_advice_text)

        if save_rpg_btn:
            save_rpg_log((
                str(rpg_date), exercises_reps, agility_drills, book_pages,
                topics_learned, tasks_solved, plan_text, plan_percent,
                total_actions, xp_earned, str_pts, agi_pts, int_pts, dsc_pts, rpg_advice_text, daily_note
            ))
            df_rpg = load_rpg_logs()
            st.success("✅ Прокачка и заметка сохранены!")

    # Лента заметок воина и график
    if not df_rpg.empty:
        st.divider()
        st.markdown("#### 📓 Лента Дневника и График XP")
        notes_df = df_rpg[df_rpg["daily_note"].fillna("") != ""]
        if not notes_df.empty:
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
# ВКЛАДКА 3: 🏆 ТРОФЕИ (СИСТЕМА ДОСТИЖЕНИЙ / АЧИВОК)
# =====================================================================
with tab_ach:
    st.markdown("#### 🏆 Зал Трофеев (Ачивки)")
    st.caption("Награды открываются автоматически при выполнении условий за день или за всё время.")

    # Проверка условий для ачивок (учитываем как базу, так и текущие ползунки)
    ach_list = [
        {
            "icon": "👁️",
            "title": "Кристальный Взгляд",
            "desc": "Удержать усталость глаз ≤ 4 без ударной нагрузки",
            "unlocked": (eye_strain <= 4 and not head_impact)
        },
        {
            "icon": "👑",
            "title": "Абсолютный Монарх (100% План)",
            "desc": "Закрыть все квесты дня на 100%",
            "unlocked": (plan_percent == 100) or (not df_rpg.empty and (df_rpg["plan_percent"] == 100).any())
        },
        {
            "icon": "🦾",
            "title": "Сотка Стали",
            "desc": "Сделать 100+ повторений упражнений за один день",
            "unlocked": (exercises_reps >= 100) or (not df_rpg.empty and (df_rpg["exercises_reps"] >= 100).any())
        },
        {
            "icon": "🥋",
            "title": "Мастер Кобудо",
            "desc": "Отработать 5+ раундов техники в воздух / с оружием",
            "unlocked": (agility_drills >= 5) or (not df_rpg.empty and (df_rpg["agility_drills"] >= 5).any())
        },
        {
            "icon": "🧠",
            "title": "Кибер-Архитектор",
            "desc": "Решить 10+ задач и прочитать 20+ страниц за день",
            "unlocked": (tasks_solved >= 10 and book_pages >= 20)
        },
        {
            "icon": "💤",
            "title": "Титановая Регенерация",
            "desc": "Проспать 8+ часов с качеством сна ≥ 8/10",
            "unlocked": (sleep_hours >= 8.0 and sleep_quality >= 8)
        }
    ]

    unlocked_count = sum(1 for a in ach_list if a["unlocked"])
    st.progress(unlocked_count / len(ach_list), text=f"Открыто трофеев: {unlocked_count} из {len(ach_list)}")

    ac1, ac2 = st.columns(2)
    for i, ach in enumerate(ach_list):
        target_col = ac1 if i % 2 == 0 else ac2
        css_cls = "ach-card ach-unlocked" if ach["unlocked"] else "ach-card ach-locked"
        status_ico = "✅ ОТКРЫТО" if ach["unlocked"] else "🔒 ЗАКРЫТО"
        with target_col:
            st.markdown(f"""
            <div class="{css_cls}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:22px; font-weight:700;">{ach['icon']} {ach['title']}</span>
                    <span class="hud-pill">{status_ico}</span>
                </div>
                <p style="margin:6px 0 0 0; font-size:13px;">{ach['desc']}</p>
            </div>
            """, unsafe_allow_html=True)


# =====================================================================
# ВКЛАДКА 4: 🧘 РЕЗЕТ (ЭКСТРЕННАЯ РАЗГРУЗКА ГЛАЗ И ЦНС)
# =====================================================================
with tab_sos:
    st.markdown("#### 🧘 Протокол экстренного восстановления (Eye & CNS Reset)")
    st.write("Если чувствуешь резь в глазах, спазм аккомодации или перегруз после учебы — запускай протокол.")

    sos_c1, sos_c2 = st.columns(2)
    with sos_c1:
        st.markdown("""
        <div class="ach-card ach-unlocked">
            <h4>🛡️ Чек-лист разгрузки</h4>
            <p>1. <b>Пальминг (60 сек):</b> Разотри ладони до тепла и прикрой закрытые глаза без давления на глазные яблоки.</p>
            <p>2. <b>Фокус вдаль:</b> Подойди к окну и зафиксируй взгляд на самой дальней точке горизонта на 30 секунд.</p>
            <p>3. <b>Дыхание 4-7-8:</b> Вдох носом (4 с) → Задержка (7 с) → Медленный выдох (8 с) для сброса кортизола.</p>
        </div>
        """, unsafe_allow_html=True)

    with sos_c2:
        st.markdown("#### ⏱️ Живой таймер Пальминга (60 секунд)")
        st.caption("Нажми кнопку, отложи телефон и закрой глаза ладонями до окончания полосы.")
        if st.button("▶️ Запустить 60 секунд Eye-Reset", use_container_width=True, type="primary"):
            bar = st.progress(0, text="Закрой глаза... Расслабь цилиарную мышцу...")
            for sec in range(1, 61):
                time.sleep(1)
                bar.progress(sec / 60.0, text=f"⏳ Идет восстановление сетчатки и фокуса: {sec} / 60 сек")
            st.success("🟢 Глаза и ЦНС разгружены! Можешь возвращаться к делам без перенапряжения.")
