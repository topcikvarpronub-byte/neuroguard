import time
from datetime import date
import streamlit as st

# Импортируем наши собственные модули из корневой папки
from database import DatabaseManager
from engine import CoreEngine

# --- 1. НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(
    page_title="NeuroGuard SaaS",
    page_icon="⚡",
    layout="wide"
)

# Инициализация БД и сессии пользователя
DatabaseManager.init_db()
if "current_user" not in st.session_state:
    st.session_state.current_user = {"id": 1, "username": "Igor_Founder", "is_pro": True}

# --- 2. САЙДБАР: АВТОРИЗАЦИЯ И МОНЕТИЗАЦИЯ ---
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
        help="Дает +25% буст к XP, золотой статус и скачивание отчетов."
    )
    if is_pro_toggle != cur_u["is_pro"]:
        DatabaseManager.set_pro_status(cur_u["id"], is_pro_toggle)
        st.session_state.current_user["is_pro"] = is_pro_toggle
        st.rerun()

    st.divider()
    dark_mode = st.toggle("🌙 Eye-Safe Mode (Тёмная тема)", value=True)

# Загружаем персональные данные пользователя
uid = st.session_state.current_user["id"]
uname = st.session_state.current_user["username"]
is_pro = st.session_state.current_user["is_pro"]

df_logs = DatabaseManager.load_health_logs(uid)
df_rpg = DatabaseManager.load_rpg_logs(uid)

# --- 3. СТИЛИ HUD-ИНТЕРФЕЙСА ---
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

tab_bio, tab_rpg, tab_ach, tab_sos, tab_rep = st.tabs([
    "🛡️ БИО",
    "⚔️ СТАТЫ",
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
            advice_parts.append("👁️ **ЗРЕНИЕ:** В норме. Соблюдай правило 20-20-20 при написании кода.")

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
            st.success("✅ Био-статус сохранен!")

    if not df_logs.empty:
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("💤 Ср. сон", f"{df_logs['sleep_hours'].mean():.1f} ч")
        m2.metric("👁️ Ср. спазм", f"{df_logs['eye_strain'].mean():.1f}/10")
        m3.metric("🔋 Ср. заряд", f"{df_logs['readiness_score'].mean():.0f}%")

        chart_df = df_logs[["log_date", "readiness_score", "eye_strain", "sleep_hours"]].sort_values("log_date")
        st.line_chart(chart_df.set_index("log_date"))

# =====================================================================
# ВКЛАДКА 2: ⚔️ СТАТЫ
# =====================================================================
with tab_rpg:
    rpg_col1, rpg_col2 = st.columns([1.1, 1])

    with rpg_col1:
        st.markdown("#### 🎯 Квесты на день")
        rpg_date = st.date_input("📅 Дата", value=date.today(), key="rpg_date")

        default_plan = "100 подтягиваний\n5 задач (ЕГЭ / Python)\n20 страниц книги\n5 раундов техники / кобудо"
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
            agility_drills = st.number_input("⚡ Раунды техники", 0, 50, 5, 1)
            book_pages = st.number_input("📖 Страницы книг", 0, 500, 20, 5)
        with rc2:
            topics_learned = st.number_input("🧠 Пройдено тем", 0, 20, 1, 1)
            tasks_solved = st.number_input("💻 Решено задач", 0, 200, 5, 1)

        daily_note = st.text_input("📓 Заметка воина (итог дня):", placeholder="Например: Сделал сотку на турнике")
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
            rpg_advice_text = "📉 **Тактика:** Дроби квесты на короткие спринты по 20 минут."
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
# ВКЛАДКА 3: 🏆 36 ТРОФЕЕВ (С ФИЛЬТРОМ ПО КАТЕГОРИЯМ)
# =====================================================================
with tab_ach:
    st.markdown("#### 🏆 Зал Славы: 36 Трофеев")

    ach_catalog = CoreEngine.evaluate_and_sync_achievements(
        uid, df_logs, df_rpg,
        eye_strain, head_impact, study_hours,
        sleep_hours, sleep_quality, current_score,
        plan_percent, exercises_reps, agility_drills,
        tasks_solved, book_pages, topics_learned, daily_note
    )

    unlocked_count = sum(1 for a in ach_catalog if a["unlocked"])
    st.progress(unlocked_count / len(ach_catalog), text=f"Открыто трофеев: {unlocked_count} из {len(ach_catalog)}")

    cat_filter = st.radio(
        "Категория трофеев:",
        ["Все (36)", "🛡️ Био и Зрение", "🥋 Спорт и ОФП", "🧠 Интеллект и Код", "👑 Дисциплина и Ранги"],
        horizontal=True
    )

    filtered_ach = [
        a for a in ach_catalog
        if cat_filter == "Все (36)" or a["category"] == cat_filter
    ]

    ac1, ac2 = st.columns(2)
    for i, ach in enumerate(filtered_ach):
        target_col = ac1 if i % 2 == 0 else ac2
        css_cls = "ach-card ach-unlocked" if ach["unlocked"] else "ach-card ach-locked"
        status_ico = f"✅ {ach['date']}" if ach["unlocked"] else "🔒 ЗАКРЫТО"
        with target_col:
            st.markdown(f"""
            <div class="{css_cls}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:17px; font-weight:700;">{ach['icon']} {ach['title']}</span>
                    <span class="hud-pill">{status_ico}</span>
                </div>
                <p style="margin:5px 0 0 0; font-size:12px;">{ach['desc']}</p>
            </div>
            """, unsafe_allow_html=True)

# =====================================================================
# ВКЛАДКА 4: 🧘 РЕЗЕТ
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
# ВКЛАДКА 5: 📄 ОТЧЕТ И ГЛОБАЛЬНЫЙ ЛИДЕРБОРД
# =====================================================================
with tab_rep:
    rep_c1, rep_c2 = st.columns([1.1, 1])

    with rep_c1:
        st.markdown("#### 📄 Официальная сводка (Для врача / тренера)")
        report_text = CoreEngine.generate_weekly_report(uname, is_pro, df_logs, df_rpg)
        st.text_area("Предпросмотр отчета:", value=report_text, height=260)

        if is_pro:
            st.download_button(
                label="📥 Скачать отчет (.TXT)",
                data=report_text.encode("utf-8"),
                file_name=f"NeuroGuard_Report_{uname}_{date.today()}.txt",
                mime="text/plain",
                use_container_width=True,
                type="primary"
            )
        else:
            st.warning("🔒 Скачивание отчета доступно в версии **💎 PRO** (включи в боковой панели слева).")

    with rep_c2:
        st.markdown("#### 🏅 Глобальный Лидерборд Игроков")
        st.caption("Рейтинг всех зарегистрированных пользователей системы по опыту (XP) и открытым трофеям.")
        df_leader = DatabaseManager.get_leaderboard()
        st.dataframe(df_leader, use_container_width=True, hide_index=True)
