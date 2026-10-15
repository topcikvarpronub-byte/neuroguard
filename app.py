import time
from datetime import date
import pandas as pd
import streamlit as st

from database import DatabaseManager
from engine import CoreEngine

# --- 1. НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(
    page_title="NeuroGuard SaaS",
    page_icon="⚡",
    layout="wide"
)

DatabaseManager.init_db()

if "page" not in st.session_state:
    st.session_state.page = "landing"

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# --- 2. ПРЕМИАЛЬНЫЙ CSS-ВИЗУАЛ ---
bg_main = "#0b0f19"
bg_card = "#131c2e"
border_col = "rgba(255, 255, 255, 0.08)"
text_col = "#f0f6fc"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;550;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background: radial-gradient(circle at 50% 0%, #162238 0%, {bg_main} 70%) !important;
        color: {text_col} !important;
        font-family: 'Inter', sans-serif !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: #0e1626 !important;
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
        background-color: #1a263f !important;
        color: {text_col} !important;
        border: 1px solid rgba(88, 166, 255, 0.2) !important;
        border-radius: 10px !important;
    }}
    .hud-row {{
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }}
    .hud-pill {{
        background: rgba(19, 28, 46, 0.8);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}
    .pro-pill {{
        border: 1px solid #f1e05a !important;
        background: linear-gradient(135deg, rgba(241,224,90,0.22), rgba(19,28,46,0.9)) !important;
        color: #f1e05a !important;
    }}
    .ach-card {{
        background: rgba(19, 28, 46, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
        border: 1px solid {border_col};
        transition: all 0.3s ease;
    }}
    .ach-card:hover {{
        border-color: rgba(88, 166, 255, 0.4);
        transform: translateY(-2px);
    }}
    .ach-unlocked {{
        border: 1px solid rgba(63, 185, 80, 0.5) !important;
        background: linear-gradient(135deg, rgba(63,185,80,0.18), rgba(19,28,46,0.85)) !important;
        box-shadow: 0 0 20px rgba(63, 185, 80, 0.15);
    }}
    .ach-locked {{
        opacity: 0.38;
    }}
    .breath-box {{
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        font-size: 22px;
        font-weight: 700;
        margin: 12px 0;
        border: 2px solid #58a6ff;
        background: rgba(88, 166, 255, 0.1);
        box-shadow: 0 0 30px rgba(88, 166, 255, 0.15);
        backdrop-filter: blur(10px);
    }}
    .landing-hero {{
        text-align: center;
        padding: 40px 20px 20px 20px;
    }}
    .section-box {{
        background: rgba(19, 28, 46, 0.6);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 30px;
        margin: 30px 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }}
    .system-footer {{
        text-align: center;
        font-size: 12px;
        color: #8b949e;
        margin-top: 40px;
        padding: 20px;
        border-top: 1px solid {border_col};
    }}
    </style>
""", unsafe_allow_html=True)


# =====================================================================
# ЭКРАН 1: 🌟 ДЛИННЫЙ ЛЕНДИНГ С КАРТИНКАМИ
# =====================================================================
if st.session_state.page == "landing":
    st.markdown("""
        <div class="landing-hero">
            <span class="hud-pill pro-pill" style="margin-bottom: 15px;">🚀 v2.5 Enterprise Edition</span>
            <h1 style="font-size: 46px; font-weight: 800; letter-spacing: -1px; margin-bottom: 15px; background: linear-gradient(90deg, #58a6ff, #3fb950); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">NEUROGUARD SaaS</h1>
            <p style="font-size: 18px; color: #8b949e; max-width: 650px; margin: 0 auto;">Интеллектуальная экосистема для глубокой продуктивности, биохакинга ЦНС и геймификации твоего потенциала.</p>
        </div>
    """, unsafe_allow_html=True)

    # Картинка 1: Hero
    try:
        st.image("hero.jpg", use_container_width=True)
    except:
        st.info("💡 Загрузите hero.jpg в корень репозитория")

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2, c_btn3 = st.columns([1, 1.2, 1])
    with c_btn2:
        if st.button("⚡ Войти в систему / Начать", use_container_width=True, type="primary"):
            st.session_state.page = "auth"
            st.rerun()

    # Секция 2: Био-мониторинг
    st.markdown("""
        <div class="section-box">
            <h2>🛡️ 1. Био-Мониторинг и Защита ЦНС</h2>
            <p style="color: #8b949e; font-size: 15px;">Интеллектуальный анализ сна, экранного времени и спазма глаз. Предиктивный алгоритм вычисляет уровень усталости и защищает от эмоционального выгорания в реальном времени.</p>
        </div>
    """, unsafe_allow_html=True)
    try:
        st.image("bio.jpg", use_container_width=True)
    except:
        pass

    # Секция 3: RPG и тепловая карта
    st.markdown("""
        <div class="section-box">
            <h2>⚔️ 2. RPG-Прокачка и GitHub Heatmap</h2>
            <p style="color: #8b949e; font-size: 15px;">Преврати рутину в увлекательную игру. Накапливай опыт (XP), повышай уровень персонажа, выполняй ежедневные квесты и отслеживай продуктивность по яркой тепловой карте.</p>
        </div>
    """, unsafe_allow_html=True)
    try:
        st.image("rpg.jpg", use_container_width=True)
    except:
        pass

    # Секция 4: Зал славы
    st.markdown("""
        <div class="section-box">
            <h2>🏆 3. Зал Славы и 36 Трофеев</h2>
            <p style="color: #8b949e; font-size: 15px;">Коллекционируй уникальные достижения за выдающиеся успехи в учебе, олимпиадах, спорте (каратэ, кобудо, ОФП) и железную дисциплину.</p>
        </div>
    """, unsafe_allow_html=True)
    try:
        st.image("trophies.jpg", use_container_width=True)
    except:
        pass

    # Секция 5: Нейро-резет
    st.markdown("""
        <div class="section-box">
            <h2>🧘 4. Нейро-Резет и Умный Советник</h2>
            <p style="color: #8b949e; font-size: 15px;">Интерактивные таймеры пальминга, правила 20-20-20, дыхательные протоколы и персональный советник по восстановлению (растяжка, сауна, холодный душ).</p>
        </div>
    """, unsafe_allow_html=True)
    try:
        st.image("reset.jpg", use_container_width=True)
    except:
        pass

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn4, c_btn5, c_btn6 = st.columns([1, 1.2, 1])
    with c_btn5:
        if st.button("🚀 Начать использовать", use_container_width=True, type="primary"):
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

    # САЙДБАР
    with st.sidebar:
        st.header("🔐 Аккаунт")
        pro_badge = "💎 PRO" if cur_u["is_pro"] else "🆓 FREE"
        st.markdown(f"Профиль: **`{cur_u['username']}`** ({pro_badge})")

        if st.button("🚪 Выйти из аккаунта", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.page = "landing"
            st.rerun()

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

    uid = cur_u["id"]
    uname = cur_u["username"]
    is_pro = cur_u["is_pro"]

    df_logs = DatabaseManager.load_health_logs(uid)
    df_rpg = DatabaseManager.load_rpg_logs(uid)

    # ВЕРХНИЙ HUD-БАР
    hist_xp = int(df_rpg["xp_earned"].sum()) if (df_rpg is not None and not df_rpg.empty and "xp_earned" in df_rpg.columns) else 0
    player_lvl = (hist_xp // 500) + 1
    last_readiness = int(df_logs.iloc[0]["readiness_score"]) if (df_logs is not None and not df_logs.empty and "readiness_score" in df_logs.columns) else 75
    rank_txt, rank_col = CoreEngine.get_rank_badge(last_readiness)
    tier_pill = '<span class="hud-pill pro-pill">💎 PRO x1.25 XP</span>' if is_pro else '<span class="hud-pill">🆓 FREE</span>'

    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; margin-bottom:12px;">
        <h3 style="margin:0; font-weight:700;">⚡ {uname}</h3>
        <div class="hud-row" style="margin:0;">
            {tier_pill}
            <span class="hud-pill" style="border-color:{rank_col}; color:{rank_col};">{rank_txt}</span>
            <span class="hud-pill">🏅 LVL {player_lvl}</span>
            <span class="hud-pill">✨ {hist_xp} XP</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_bio, tab_rpg, tab_goals, tab_ach, tab_sos, tab_rep = st.tabs([
        "🛡️ БИО",
        "⚔️ СТАТЫ",
        "🎯 ЦЕЛИ",
        "🏆 36 ТРОФЕЕВ",
        "🧘 РЕЗЕТ",
        "📄 ОТЧЕТ & ТОП"
    ])

    # ВКЛАДКА 1: 🛡️ БИО
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

            if analyze_btn:
                DatabaseManager.save_health_log((
                    uid, str(log_date), sleep_hours, sleep_quality, study_hours,
                    eye_strain, training_type, training_intensity,
                    int(head_impact), current_score, burnout['message']
                ))
                st.success("✅ Био-статус сохранен!")
                st.rerun()

    # ВКЛАДКА 2: ⚔️ СТАТЫ & ГИТХАБ-ТЕПЛОВАЯ КАРТА
    with tab_rpg:
        rpg_col1, rpg_col2 = st.columns([1.1, 1])
        with rpg_col1:
            st.markdown("#### 🎯 Квесты на день")
            rpg_date = st.date_input("📅 Дата", value=date.today(), key="rpg_date")

            default_plan = "100 подтягиваний\n5 задач (ЕГЭ / Python)\n20 страниц книги\n5 раундов техники / кобудо"
            plan_text = st.text_area("Список задач:", value=default_plan, height=100)

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
            st.markdown("#### 🧬 Характеристики Персонажа")
            str_pts, agi_pts, int_pts, dsc_pts, total_actions, xp_earned = CoreEngine.calculate_rpg_stats(
                exercises_reps, agility_drills, book_pages, topics_learned, tasks_solved, plan_percent, is_pro=is_pro
            )

            st.markdown(f"""
            <div class="hud-row">
                <span class="hud-pill">🎯 План: {plan_percent}%</span>
                <span class="hud-pill">✨ +{xp_earned} XP</span>
            </div>
            """, unsafe_allow_html=True)

            if save_rpg_btn:
                DatabaseManager.save_rpg_log((
                    uid, str(rpg_date), exercises_reps, agility_drills, book_pages,
                    topics_learned, tasks_solved, plan_text, plan_percent,
                    total_actions, xp_earned, str_pts, agi_pts, int_pts, dsc_pts, "Активен", daily_note
                ))
                st.success("✅ Статы сохранены в БД!")
                st.rerun()

        st.divider()
        st.markdown("#### 🔥 Тепловая карта активности (GitHub-Style Heatmap)")
        if df_rpg is not None and not df_rpg.empty and "log_date" in df_rpg.columns and "plan_percent" in df_rpg.columns:
            heat_df = df_rpg[["log_date", "plan_percent"]].sort_values("log_date")
            st.bar_chart(heat_df.set_index("log_date"), color="#3fb950")
        else:
            st.info("Сохрани первый RPG-лог выше, чтобы активировать тепловую карту!")

    # ВКЛАДКА 3: 🎯 ЦЕЛИ
    with tab_goals:
        st.markdown("#### 🎯 Глобальные Цели на Месяц и Год")
        with st.expander("➕ Добавить новую цель"):
            new_period = st.selectbox("Период", ["Месяц", "Год"])
            p_val = "month" if new_period == "Месяц" else "year"
            new_title = st.text_input("Название цели", placeholder="Например: Сдать экзамен на 90+")
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

    # ВКЛАДКА 4: 🏆 36 ТРОФЕЕВ
    with tab_ach:
        st.markdown("#### 🏆 Зал Славы: 36 Трофеев")
        ach_catalog = CoreEngine.evaluate_and_sync_achievements(
            uid, df_logs, df_rpg, 3, False, 5.0, 7.5, 8, 75, 70, 100, 3, 5, 20, 1, ""
        )
        unlocked_count = sum(1 for a in ach_catalog if a["unlocked"])
        st.progress(unlocked_count / len(ach_catalog), text=f"Открыто трофеев: {unlocked_count} из {len(ach_catalog)}")

        ac1, ac2 = st.columns(2)
        for i, ach in enumerate(ach_catalog):
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
                    <p style="margin:6px 0 0 0; font-size:12px; color:#8b949e;">{ach['desc']}</p>
                </div>
                """, unsafe_allow_html=True)

    # ВКЛАДКА 5: 🧘 РЕЗЕТ
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

    # ВКЛАДКА 6: 📄 ОТЧЕТ & ТОП
    with tab_rep:
        rep_c1, rep_c2 = st.columns([1.1, 1])
        with rep_c1:
            st.markdown("#### 📄 Официальная сводка")
            report_text = CoreEngine.generate_weekly_report(uname, is_pro, df_logs, df_rpg)
            st.text_area("Предпросмотр:", value=report_text, height=220)
        with rep_c2:
            st.markdown("#### 🏅 Глобальный Лидерборд")
            df_leader = DatabaseManager.get_leaderboard()
            if df_leader is not None and not df_leader.empty:
                st.dataframe(df_leader, use_container_width=True, hide_index=True)
            else:
                st.info("Пока нет участников в таблице лидеров.")
