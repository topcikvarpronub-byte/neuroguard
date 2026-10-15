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
if "current_user" not in st.session_state:
    st.session_state.current_user = {"id": 1, "username": "Igor_Founder", "is_pro": True}

# --- 2. САЙДБАР ---
with st.sidebar:
    st.header("🔐 Аккаунт (SaaS Auth)")
    cur_u = st.session_state.current_user
    pro_badge = "💎 PRO" if cur_u["is_pro"] else "🆓 FREE"
    st.markdown(f"Профиль: **`{cur_u['username']}`** ({pro_badge})")

    with st.expander("🔄 Сменить / Создать профиль"):
        auth_mode = st.radio("Режим:", ["Вход", "Регистрация"], horizontal=True)
        inp_user = st.text_input("Никнейм", value=cur_u["username"])
        inp_pin = st.text_input("PIN-код", value="0000", type="password", max_chars=8)
        if st.button("🚀 Применить", use_container_width=True):
            user_obj, err = DatabaseManager.authenticate_or_register(
                inp_user, inp_pin, create_new=(auth_mode == "Регистрация")
            )
            if err:
                st.error(err)
            else:
                st.session_state.current_user = user_obj
                st.success(f"Профиль {user_obj['username']} активен!")
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

uid = st.session_state.current_user["id"]
uname = st.session_state.current_user["username"]
is_pro = st.session_state.current_user["is_pro"]

df_logs = DatabaseManager.load_health_logs(uid)
df_rpg = DatabaseManager.load_rpg_logs(uid)

# --- 3. СТИЛИ И ЦВЕТА ---
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
        padding: 12px;
        margin-bottom: 10px;
        border: 1px solid {border_col};
    }}
    .ach-unlocked {{
        border: 1px solid #3fb950 !important;
        background: linear-gradient(135deg, rgba(63,185,80,0.14), rgba(22,27,34,0.9));
    }}
    .ach-locked {{
        opacity: 0.42;
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

# --- 4. ВЕРХНИЙ HUD-БАР ---
hist_xp = int(df_rpg["xp_earned"].sum()) if (df_rpg is not None and not df_rpg.empty and "xp_earned" in df_rpg.columns) else 0
player_lvl = (hist_xp // 500) + 1
last_readiness = int(df_logs.iloc[0]["readiness_score"]) if (df_logs is not None and not df_logs.empty and "readiness_score" in df_logs.columns) else 75
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

tab_bio, tab_rpg, tab_goals, tab_ach, tab_sos, tab_rep = st.tabs([
    "🛡️ БИО",
    "⚔️ СТАТЫ",
    "🎯 ЦЕЛИ",
    "🏆 36 ТРОФЕЕВ",
    "🧘 РЕЗЕТ",
    "📄 ОТЧЕТ & ТОП"
])

# =====================================================================
# ВКЛАДКА 1: 🛡️ БИО
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
        <div style="background-color:{burnout['color']}22; border:1px solid {burnout['color']}; border-radius:10px; padding:10px; margin-top:10px;">
            <b style="color:{burnout['color']};">{burnout['risk_level']}</b><br>
            <p style="margin:5px 0 0 0; font-size:13px;">{burnout['message']}</p>
        </div>
        """, unsafe_allow_html=True)

        if analyze_btn:
            DatabaseManager.save_health_log((
                uid, str(log_date), sleep_hours, sleep_quality, study_hours,
                eye_strain, training_type, training_intensity,
                int(head_impact), current_score, burnout['message']
            ))
            st.success("✅ Био-статус сохранен! Перезагрузи страницу.")
            st.rerun()

# =====================================================================
# ВКЛАДКА 2: ⚔️ СТАТЫ & ГИТХАБ-ТЕПЛОВАЯ КАРТА
# =====================================================================
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

# =====================================================================
# ВКЛАДКА 3: 🎯 ГЛОБАЛЬНЫЕ ЦЕЛИ
# =====================================================================
with tab_goals:
    st.markdown("#### 🎯 Глобальные Цели на Месяц и Год")
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

                new_val = st.number_input(f"Обновить: {title}", value=float(curr), key=f"goal_inp_{gid}", step=1.0)
                if new_val != curr:
                    DatabaseManager.update_goal_progress(gid, new_val)
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

                new_val = st.number_input(f"Обновить: {title}", value=float(curr), key=f"goal_inp_{gid}", step=10.0)
                if new_val != curr:
                    DatabaseManager.update_goal_progress(gid, new_val)
                    st.rerun()
                st.divider()

# =====================================================================
# ВКЛАДКА 4: 🏆 36 ТРОФЕЕВ
# =====================================================================
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
                <p style="margin:4px 0 0 0; font-size:12px;">{ach['desc']}</p>
            </div>
            """, unsafe_allow_html=True)

# =====================================================================
# ВКЛАДКА 5: 🧘 РЕЗЕТ
# =====================================================================
with tab_sos:
    st.markdown("#### 🧘 Нейро-Резет: Разгрузка сетчатки и ЦНС")
    if st.button("▶️ Запустить 60 сек Пальминга", use_container_width=True, type="primary"):
        bar = st.progress(0, text="Расслабь глаза...")
        for sec in range(1, 61):
            bar.progress(sec / 60.0)
            time.sleep(1)
        st.success("✅ Пальминг завершен!")

# =====================================================================
# ВКЛАДКА 6: 📄 ОТЧЕТ & ТОП
# =====================================================================
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
