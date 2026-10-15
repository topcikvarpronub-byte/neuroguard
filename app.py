import os
import time
from datetime import date
import streamlit as st
import pandas as pd

# ==============================================================================
# МОДУЛЬНЫЕ ИМПОРТЫ ИЗ ТВОИХ ФАЙЛОВ РЕПОЗИТОРИЯ
# ==============================================================================
from database import DatabaseManager
from engine import CoreEngine
from achievements_data import ACHIEVEMENTS_CATALOG
from library_data import SKINS_CATALOG, WORKOUT_PROTOCOLS, LIBRARY_CATALOG

# ==============================================================================
# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ И ИНИЦИАЛИЗАЦИЯ БАЗЫ
# ==============================================================================
st.set_page_config(
    page_title="NeuroGuard OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

DatabaseManager.init_db()

# ==============================================================================
# 2. ЖЕЛЕЗОБЕТОННОЕ СОХРАНЕНИЕ СЕССИИ И СОСТОЯНИЙ
# ==============================================================================
if "user" not in st.session_state:
    st.session_state.user = None

# Авто-восстановление сессии при перезагрузке страницы через URL-параметры
if st.session_state.user is None and "u" in st.query_params and "p" in st.query_params:
    u_param = st.query_params["u"]
    p_param = st.query_params["p"]
    user_obj, _ = DatabaseManager.authenticate_or_register(u_param, p_param, create_new=False)
    if user_obj:
        st.session_state.user = user_obj

if "active_skin" not in st.session_state:
    st.session_state.active_skin = "cyber_blue"

if "morning_intent" not in st.session_state:
    st.session_state.morning_intent = ""

if "intent_locked" not in st.session_state:
    st.session_state.intent_locked = False

if "habits" not in st.session_state:
    st.session_state.habits = {
        "Гидратация (2.5л чистой воды)": False,
        "Зрение: Протокол 20-20-20 и пальминг": False,
        "Алгоритмы / Код (минимум 60 минут фокуса)": False,
        "Физическая база / Суставная разминка": False,
        "Чтение профильной литературы (30+ стр.)": False,
        "Цифровой детокс за 1 час до сна": False
    }

if "pr_records" not in st.session_state:
    st.session_state.pr_records = {
        "Подтягивания за 14 мин (повторений)": 100,
        "Закрытый горизонт (секунд)": 15,
        "Жим штанги лежа (кг)": 95,
        "Бег 5 км (минут)": 21.5
    }

# ==============================================================================
# 3. ДИНАМИЧЕСКАЯ СТИЛИЗАЦИЯ (LINEAR / NOTION DARK UI)
# ==============================================================================
skin_key = st.session_state.active_skin
if skin_key not in SKINS_CATALOG:
    skin_key = "cyber_blue"

current_skin = SKINS_CATALOG[skin_key]
accent_col = current_skin["accent"]
glow_col = current_skin["glow"]

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #0d1117;
        color: #e6edf3;
    }}

    /* Убираем стандартные стрелочки в экспандерах и лишний декор */
    details > summary {{
        list-style: none;
    }}
    details > summary::-webkit-details-marker {{
        display: none;
    }}

    /* Карточки в стиле Linear */
    .linear-card {{
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 14px;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    .linear-card:hover {{
        border-color: {accent_col};
        box-shadow: 0 4px 20px {glow_col};
    }}

    /* Метрики */
    .metric-box {{
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #30363d;
        border-left: 3px solid {accent_col};
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }}
    .metric-label {{
        font-size: 0.78rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }}
    .metric-value {{
        font-size: 1.55rem;
        font-weight: 700;
        color: #f0f6fc;
        margin-top: 4px;
    }}

    /* Бейджи */
    .pill-badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid #30363d;
        color: {accent_col};
    }}

    /* Трофеи */
    .trophy-card {{
        background: #12161c;
        border: 1px solid #21262d;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
        opacity: 0.55;
    }}
    .trophy-unlocked {{
        background: #161b22;
        border: 1px solid {accent_col};
        box-shadow: 0 0 14px {glow_col};
        opacity: 1.0;
    }}

    /* Кастомный прогресс-бар */
    .xp-bar-bg {{
        width: 100%;
        height: 8px;
        background: #21262d;
        border-radius: 999px;
        overflow: hidden;
        margin: 8px 0;
    }}
    .xp-bar-fill {{
        height: 100%;
        background: {accent_col};
        border-radius: 999px;
    }}
</style>
""", unsafe_allow_html=True)


def show_banner_if_exists(filename: str):
    """Безопасный вывод обложек разделов из репозитория"""
    if os.path.exists(filename):
        st.image(filename, use_container_width=True)


# ==============================================================================
# 4. АВТОРИЗАЦИЯ (ЕСЛИ ПОЛЬЗОВАТЕЛЬ НЕ ВОШЕЛ)
# ==============================================================================
if st.session_state.user is None:
    show_banner_if_exists("hero.jpg")
    st.markdown("<h2 style='margin-bottom: 4px;'>⚡ NeuroGuard Workspace</h2>", unsafe_allow_html=True)
    st.caption("Модульная операционная система биохакинга, аналитики ЦНС и продуктивности.")

    col_auth1, col_auth2 = st.columns([1.2, 1])
    with col_auth1:
        st.markdown("""
        <div class="linear-card">
            <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 8px;">Единое рабочее пространство</div>
            <div style="font-size: 0.88rem; color: #8b949e; line-height: 1.5;">
                • <b>Мониторинг ЦНС и зрения:</b> контроль экранной нагрузки и качества восстановления.<br>
                • <b>Аналитика прогресса:</b> автоматический расчёт опыта, уровней и продуктивности.<br>
                • <b>Зал Славы:</b> 100 достижений с синхронизацией в реальном времени.<br>
                • <b>База знаний и протоколы:</b> тренировочные циклы и профильная библиотека.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Быстрый вход (Профиль Основателя: Igor_Founder)", use_container_width=True):
            user_obj, err = DatabaseManager.authenticate_or_register("Igor_Founder", "0000", create_new=False)
            if user_obj:
                st.session_state.user = user_obj
                st.query_params["u"] = "Igor_Founder"
                st.query_params["p"] = "0000"
                st.rerun()

    with col_auth2:
        auth_mode = st.radio("Режим доступа", ["Вход в систему", "Регистрация профиля"], horizontal=True)
        u_input = st.text_input("Никнейм оператора", value="Igor_Founder")
        p_input = st.text_input("PIN-код доступа", value="0000", type="password")

        if st.button("Подтвердить доступ", type="primary", use_container_width=True):
            is_new = (auth_mode == "Регистрация профиля")
            user_obj, err = DatabaseManager.authenticate_or_register(u_input, p_input, create_new=is_new)
            if err:
                st.error(err)
            else:
                st.session_state.user = user_obj
                st.query_params["u"] = u_input
                st.query_params["p"] = p_input
                st.rerun()

    st.stop()


# ==============================================================================
# 5. ЗАГРУЗКА ДАННЫХ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ И РАСЧЕТ ПАРАМЕТРОВ
# ==============================================================================
user = st.session_state.user
user_id = user["id"]
username = user["username"]
is_pro = user["is_pro"]

df_health = DatabaseManager.load_health_logs(user_id)
df_rpg = DatabaseManager.load_rpg_logs(user_id)

total_xp = int(df_rpg["xp_earned"].sum()) if not df_rpg.empty else 0
user_lvl = (total_xp // 500) + 1
xp_in_curr_lvl = total_xp % 500
xp_progress_pct = int((xp_in_curr_lvl / 500.0) * 100)

last_readiness = int(df_health.iloc[0]["readiness_score"]) if not df_health.empty else 85
rank_title, rank_color = CoreEngine.get_rank_badge(last_readiness)
burnout_info = CoreEngine.analyze_burnout_risk(df_health, df_rpg)

# Синхронизация всех 100 достижений через CoreEngine
curr_eye = int(df_health.iloc[0]["eye_strain"]) if not df_health.empty else 3
curr_impact = bool(df_health.iloc[0]["head_impact"]) if not df_health.empty else False
curr_study = float(df_health.iloc[0]["study_hours"]) if not df_health.empty else 4.0
curr_sleep = float(df_health.iloc[0]["sleep_hours"]) if not df_health.empty else 8.0
curr_sleep_q = int(df_health.iloc[0]["sleep_quality"]) if not df_health.empty else 8

curr_plan = int(df_rpg.iloc[0]["plan_percent"]) if not df_rpg.empty else 0
curr_reps = int(df_rpg.iloc[0]["exercises_reps"]) if not df_rpg.empty else 0
curr_drills = int(df_rpg.iloc[0]["agility_drills"]) if not df_rpg.empty else 0
curr_tasks = int(df_rpg.iloc[0]["tasks_solved"]) if not df_rpg.empty else 0
curr_pages = int(df_rpg.iloc[0]["book_pages"]) if not df_rpg.empty else 0
curr_topics = int(df_rpg.iloc[0]["topics_learned"]) if not df_rpg.empty else 0
curr_note = str(df_rpg.iloc[0]["daily_note"]) if not df_rpg.empty else ""

synced_achievements = CoreEngine.evaluate_and_sync_achievements(
    user_id=user_id,
    df_health=df_health,
    df_rpg=df_rpg,
    curr_eye=curr_eye,
    curr_impact=curr_impact,
    curr_study=curr_study,
    curr_sleep=curr_sleep,
    curr_sleep_q=curr_sleep_q,
    curr_readiness=last_readiness,
    curr_plan=curr_plan,
    curr_reps=curr_reps,
    curr_drills=curr_drills,
    curr_tasks=curr_tasks,
    curr_pages=curr_pages,
    curr_topics=curr_topics,
    curr_note=curr_note
)
unlocked_count = sum(1 for a in synced_achievements if a["unlocked"])


# ==============================================================================
# 6. БОКОВАЯ ПАНЕЛЬ: ПРОФИЛЬ, ВЫБОР СКИНА И ЭКСПОРТ В ОДИН КЛИК
# ==============================================================================
with st.sidebar:
    st.markdown(f"""
    <div class="linear-card" style="padding: 16px;">
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <div style="font-size: 1.8rem;">{current_skin['avatar']}</div>
            <span class="pill-badge">{'💎 PRO' if is_pro else 'FREE'}</span>
        </div>
        <div style="font-weight: 700; font-size: 1.1rem; margin-top: 8px;">{username}</div>
        <div style="font-size: 0.8rem; color: #8b949e;">{current_skin['role']} • <span style="color:{rank_color}; font-weight:600;">{rank_title}</span></div>
        <div style="margin-top: 12px; font-size: 0.78rem; display:flex; justify-content:space-between;">
            <span>Уровень {user_lvl}</span>
            <span style="color:{accent_col}; font-weight:600;">{total_xp} XP ({xp_in_curr_lvl}/500)</span>
        </div>
        <div class="xp-bar-bg">
            <div class="xp-bar-fill" style="width: {xp_progress_pct}%;"></div>
        </div>
        <div style="font-size: 0.75rem; color: #8b949e; margin-top: 6px;">
            Трофеев открыто: <b>{unlocked_count} / {len(ACHIEVEMENTS_CATALOG)}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### 🎨 Тема оформления (Скины)")
    skin_options = list(SKINS_CATALOG.keys())
    selected_skin = st.selectbox(
        "Визуальный профиль",
        options=skin_options,
        index=skin_options.index(skin_key),
        format_func=lambda k: f"{SKINS_CATALOG[k]['avatar']} {SKINS_CATALOG[k]['name']} (LVL {SKINS_CATALOG[k]['min_lvl']}+)"
    )

    if selected_skin != skin_key:
        req_lvl = SKINS_CATALOG[selected_skin]["min_lvl"]
        if user_lvl >= req_lvl or is_pro:
            st.session_state.active_skin = selected_skin
            st.rerun()
        else:
            st.warning(f"Для этой темы требуется Уровень {req_lvl} или статус PRO.")

    st.caption(SKINS_CATALOG[skin_key]["desc"])
    st.divider()

    # Управление PRO-статусом
    pro_toggle = st.toggle("💎 Активировать PRO-режим (+25% XP)", value=is_pro)
    if pro_toggle != is_pro:
        DatabaseManager.set_pro_status(user_id, pro_toggle)
        st.session_state.user["is_pro"] = pro_toggle
        st.rerun()

    # Экспорт отчета в один клик
    report_text = CoreEngine.generate_weekly_report(username, is_pro, df_health, df_rpg)
    st.download_button(
        label="📥 Скачать сводку (TXT)",
        data=report_text.encode("utf-8"),
        file_name=f"neuroguard_report_{date.today()}.txt",
        mime="text/plain",
        use_container_width=True
    )

    if st.button("Выйти из профиля", use_container_width=True):
        st.session_state.user = None
        st.query_params.clear()
        st.rerun()


# ==============================================================================
# 7. ГЛАВНАЯ НАВИГАЦИЯ ПО РАЗДЕЛАМ
# ==============================================================================
tabs = st.tabs([
    "🧭 Дашборд",
    "🛡️ Биометрия & ЦНС",
    "⚔️ Продуктивность & RPG",
    "🧘 Протоколы & Тренировки",
    "🏆 Зал Славы & Цели",
    "📚 База Знаний"
])


# ------------------------------------------------------------------------------
# ВКЛАДКА 1: ДАШБОРД, УТРЕННЯЯ ДЕКЛАРАЦИЯ И ТРЕКЕР ПРИВЫЧЕК
# ------------------------------------------------------------------------------
with tabs[0]:
    show_banner_if_exists("hero.jpg")

    # Верхний ряд ключевых показателей
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Готовность ЦНС</div>
            <div class="metric-value">{last_readiness}%</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Уровень и Опыт</div>
            <div class="metric-value">LVL {user_lvl} <span style="font-size:0.9rem; color:#8b949e;">({total_xp} XP)</span></div>
        </div>
        """, unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Достижения</div>
            <div class="metric-value">{unlocked_count} / 100</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col4:
        st.markdown(f"""
        <div class="metric-box" style="border-left-color: {burnout_info['color']};">
            <div class="metric-label">Статус нагрузки</div>
            <div class="metric-value" style="font-size: 1.05rem; color: {burnout_info['color']}; margin-top: 10px;">
                {burnout_info['risk_level']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="linear-card" style="border-left: 4px solid {burnout_info['color']};">
        <div style="font-weight: 600; margin-bottom: 4px;">Аналитика состояния системы</div>
        <div style="font-size: 0.9rem; color: #c9d1d9;">{burnout_info['message']}</div>
    </div>
    """, unsafe_allow_html=True)

    col_d1, col_d2 = st.columns([1.15, 1])

    # Утреннее окно декларации намерений
    with col_d1:
        st.markdown("##### 🎯 Декларация фокуса на день")
        st.caption("Сформулируй одну главную задачу, которая сделает сегодняшний день результативным.")

        intent_val = st.text_input(
            "Ключевой приоритет дня",
            value=st.session_state.morning_intent,
            placeholder="Например: Решить 10 задач по информатике и провести силовую тренировку без перегруза ЦНС",
            label_visibility="collapsed"
        )
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("Зафиксировать вектор дня", type="primary", use_container_width=True):
                st.session_state.morning_intent = intent_val
                st.session_state.intent_locked = True
        with c_btn2:
            if st.button("Сбросить фокус", use_container_width=True):
                st.session_state.morning_intent = ""
                st.session_state.intent_locked = False
                st.rerun()

        if st.session_state.intent_locked and st.session_state.morning_intent:
            st.markdown(f"""
            <div class="linear-card" style="border-color: {accent_col}; margin-top: 10px;">
                <span class="pill-badge">АКТИВНЫЙ ФОКУС</span>
                <div style="font-weight: 600; font-size: 1.02rem; margin-top: 8px;">{st.session_state.morning_intent}</div>
            </div>
            """, unsafe_allow_html=True)

        # Личные рекорды (PR)
        st.markdown("##### ⚡ Личные нормативы и рекорды (PR)")
        pr_cols = st.columns(2)
        for idx, (pr_name, pr_val) in enumerate(st.session_state.pr_records.items()):
            with pr_cols[idx % 2]:
                new_pr = st.number_input(pr_name, value=float(pr_val), step=1.0, key=f"pr_{idx}")
                st.session_state.pr_records[pr_name] = new_pr

    # Чек-лист ежедневных привычек
    with col_d2:
        st.markdown("##### ✅ Ежедневный протокол дисциплины")
        st.caption("Отмечай базовые привычки для поддержания ресурса ЦНС и фокуса.")

        completed_habits = 0
        for h_name in list(st.session_state.habits.keys()):
            st.session_state.habits[h_name] = st.checkbox(h_name, value=st.session_state.habits[h_name])
            if st.session_state.habits[h_name]:
                completed_habits += 1

        habit_pct = int((completed_habits / len(st.session_state.habits)) * 100)
        st.progress(habit_pct / 100.0, text=f"Выполнение протокола привычек: {habit_pct}%")


# ------------------------------------------------------------------------------
# ВКЛАДКА 2: БИОМЕТРИЯ, ЗРЕНИЕ И КОНТРОЛЬ ЦНС
# ------------------------------------------------------------------------------
with tabs[1]:
    show_banner_if_exists("bio.jpg")
    st.markdown("#### 🛡️ Мониторинг биометрии, зрения и ресурса ЦНС")
    st.caption("Записывай показатели сна и зрительной нагрузки для точного расчёта индекса готовности (Readiness).")

    b_col1, b_col2 = st.columns([1.1, 1])

    with b_col1:
        with st.form("bio_log_form"):
            log_d = st.date_input("Дата записи", value=date.today())
            c_sl1, c_sl2 = st.columns(2)
            with c_sl1:
                sleep_h = st.slider("Продолжительность сна (часов)", 3.0, 12.0, 8.0, 0.5)
                study_h = st.slider("Экранное время / учеба и код (часов)", 0.0, 16.0, 5.0, 0.5)
            with c_sl2:
                sleep_q = st.slider("Качество сна (1–10)", 1, 10, 8)
                eye_strain = st.slider("Усталость глаз / спазм (1–10)", 1, 10, 3)

            train_type = st.selectbox(
                "Основной тип физической нагрузки",
                ["Отдых / Восстановление", "Калистеника / Турники (ОФП)", "Техника / Кобудо / Бой с тенью", "Силовая в зале", "Спарринги / Соревнования", "Кардио / Бег"]
            )
            train_int = st.slider("Интенсивность тренировки (0–10)", 0, 10, 5)
            head_impact = st.checkbox("⚠️ Была ударная нагрузка на голову или жесткое натуживание")

            submitted_bio = st.form_submit_button("Рассчитать индекс и сохранить в базу", type="primary", use_container_width=True)

            if submitted_bio:
                r_score = CoreEngine.calculate_readiness(
                    sleep_h=sleep_h,
                    sleep_q=sleep_q,
                    study_h=study_h,
                    eye_strain=eye_strain,
                    train_int=train_int,
                    head_impact=head_impact
                )
                temp_df = pd.DataFrame([{
                    "training_type": train_type,
                    "training_intensity": train_int,
                    "head_impact": int(head_impact),
                    "eye_strain": eye_strain
                }])
                advice_str = CoreEngine.generate_recovery_advice(temp_df)

                DatabaseManager.save_health_log((
                    user_id, str(log_d), sleep_h, sleep_q, study_h,
                    eye_strain, train_type, train_int, int(head_impact),
                    r_score, advice_str
                ))
                st.success(f"Запись сохранена! Индекс готовности ЦНС: {r_score}%")
                st.rerun()

    with b_col2:
        st.markdown("##### 🤖 Персональный протокол восстановления")
        rec_advice = CoreEngine.generate_recovery_advice(df_health)
        st.info(rec_advice)

        if not df_health.empty:
            st.markdown("##### 📊 Динамика готовности ЦНС и сна")
            chart_df = df_health[["log_date", "readiness_score", "sleep_hours"]].sort_values("log_date")
            st.dataframe(df_health[["log_date", "sleep_hours", "eye_strain", "training_type", "readiness_score"]].head(7), use_container_width=True, hide_index=True)


# ------------------------------------------------------------------------------
# ВКЛАДКА 3: ПРОДУКТИВНОСТЬ & RPG-СТАТИСТИКА
# ------------------------------------------------------------------------------
with tabs[2]:
    show_banner_if_exists("rpg.jpg")
    st.markdown("#### ⚔️ Трекинг действий, учёбы и тренировочного объёма")
    st.caption("Каждое выполненное действие конвертируется в очки характеристик (STR, AGI, INT, DSC) и опыт профиля.")

    r_col1, r_col2 = st.columns([1.15, 1])

    with r_col1:
        with st.form("rpg_log_form"):
            rpg_date = st.date_input("Дата отчёта", value=date.today(), key="rpg_d")
            rc1, rc2 = st.columns(2)
            with rc1:
                ex_reps = st.number_input("Силовые повторения (подтягивания, отжимания, зал)", 0, 2000, 100, step=10)
                agi_drills = st.number_input("Раунды техники / боя с тенью / кобудо", 0, 50, 5, step=1)
                pages = st.number_input("Прочитано страниц книг", 0, 500, 25, step=5)
            with rc2:
                tasks = st.number_input("Решено задач (ЕГЭ / Python / Алгоритмы)", 0, 200, 10, step=1)
                topics = st.number_input("Разобрано новых тем / модулей", 0, 30, 2, step=1)
                plan_pct = st.slider("Выполнение плана дня (%)", 0, 100, 90, step=5)

            plan_text = st.text_input("Ключевые закрытые задачи дня", placeholder="Укажи главные выполненные блоки...")
            daily_note = st.text_area("Заметка оператора (рефлексия и выводы)", placeholder="Что сработало отлично, а что нужно скорректировать завтра...")

            sub_rpg = st.form_submit_button("Зафиксировать результат и начислить XP", type="primary", use_container_width=True)

            if sub_rpg:
                str_pts, agi_pts, int_pts, dsc_pts, total_act, xp_gain = CoreEngine.calculate_rpg_stats(
                    ex_reps=ex_reps,
                    agi_drills=agi_drills,
                    pages=pages,
                    topics=topics,
                    tasks=tasks,
                    plan_pct=plan_pct,
                    is_pro=is_pro
                )
                rpg_msg = f"Начислено +{xp_gain} XP | STR +{str_pts}, AGI +{agi_pts}, INT +{int_pts}, DSC +{dsc_pts}"

                DatabaseManager.save_rpg_log((
                    user_id, str(rpg_date), ex_reps, agi_drills, pages,
                    topics, tasks, plan_text, plan_pct, total_act,
                    xp_gain, str_pts, agi_pts, int_pts, dsc_pts, rpg_msg, daily_note
                ))
                st.success(f"Отчёт сохранён! {rpg_msg}")
                st.rerun()

    with r_col2:
        st.markdown("##### 📈 Суммарные характеристики оператора")
        sum_str = int(df_rpg["str_pts"].sum()) if not df_rpg.empty else 0
        sum_agi = int(df_rpg["agi_pts"].sum()) if not df_rpg.empty else 0
        sum_int = int(df_rpg["int_pts"].sum()) if not df_rpg.empty else 0
        sum_dsc = int(df_rpg["dsc_pts"].sum()) if not df_rpg.empty else 0

        sc1, sc2 = st.columns(2)
        sc1.metric("🦾 Сила (STR)", sum_str)
        sc2.metric("⚡ Ловкость и Техника (AGI)", sum_agi)
        sc1.metric("🧠 Интеллект и Код (INT)", sum_int)
        sc2.metric("👑 Дисциплина (DSC)", sum_dsc)

        if not df_rpg.empty:
            st.markdown("##### 🗂️ История последних отчётов")
            st.dataframe(
                df_rpg[["log_date", "xp_earned", "exercises_reps", "tasks_solved", "plan_percent"]].head(7),
                use_container_width=True,
                hide_index=True
            )


# ------------------------------------------------------------------------------
# ВКЛАДКА 4: ТРЕНИРОВОЧНЫЕ ПРОТОКОЛЫ, РЕЗЕТ ЦНС И ТАЙМЕР
# ------------------------------------------------------------------------------
with tabs[3]:
    show_banner_if_exists("reset.jpg")
    st.markdown("#### 🧘 Тренировочные протоколы и таймер рабочей сессии")

    p_col1, p_col2 = st.columns([1.25, 1])

    with p_col1:
        st.markdown("##### 🥋 Протоколы тренировок (из `library_data.py`)")
        selected_proto = st.selectbox("Выбери тренировочный комплекс", list(WORKOUT_PROTOCOLS.keys()))

        st.markdown('<div class="linear-card">', unsafe_allow_html=True)
        st.markdown(f"**Комплекс: {selected_proto}**")
        for idx, step_text in enumerate(WORKOUT_PROTOCOLS[selected_proto], start=1):
            st.checkbox(f"{idx}. {step_text}", key=f"proto_{selected_proto}_{idx}")
        st.markdown('</div>', unsafe_allow_html=True)

    with p_col2:
        st.markdown("##### ⏱️ Таймер интервальной работы / резета зрения")
        st.caption("Используй для статики (удержание горизонта, вис), раундов боя с тенью или гимнастики для глаз.")

        timer_presets = {
            "Статика / Удержание горизонта (15 сек)": 15,
            "Релаксация глаз / Пальминг (60 сек)": 60,
            "Вис на перекладине / Декомпрессия (90 сек)": 90,
            "Раунд боя с тенью / Кобудо (180 сек)": 180
        }
        chosen_preset = st.selectbox("Режим таймера", list(timer_presets.keys()))
        seconds_to_run = st.number_input("Длительность (секунд)", min_value=5, max_value=600, value=timer_presets[chosen_preset], step=5)

        if st.button("▶️ Запустить таймер", type="primary", use_container_width=True):
            progress_bar = st.progress(0.0)
            status_txt = st.empty()
            for rem in range(int(seconds_to_run), 0, -1):
                pct = (seconds_to_run - rem) / float(seconds_to_run)
                progress_bar.progress(pct)
                status_txt.markdown(f"<h3 style='text-align:center; color:{accent_col};'>Осталось: {rem} сек.</h3>", unsafe_allow_html=True)
                time.sleep(1)
            progress_bar.progress(1.0)
            status_txt.success("✅ Сессия успешно завершена!")


# ------------------------------------------------------------------------------
# ВКЛАДКА 5: ЗАЛ СЛАВЫ (100 ДОСТИЖЕНИЙ), ЦЕЛИ И ЛИДЕРБОРД
# ------------------------------------------------------------------------------
with tabs[4]:
    show_banner_if_exists("trophies.jpg")

    g_tab1, g_tab2, g_tab3 = st.tabs([
        f"🏆 Зал Славы ({unlocked_count}/100)",
        "🎯 Стратегические Цели",
        "🌐 Таблица Лидеров"
    ])

    # Подвкладка 1: Все 100 достижений из achievements_data.py
    with g_tab1:
        st.markdown("##### 🏆 Полный каталог 100 достижений системы")
        all_categories = sorted(list(set(item["category"] for item in synced_achievements)))

        f_col1, f_col2 = st.columns([1.3, 1])
        with f_col1:
            selected_cat = st.selectbox("Фильтр по категории", ["Все категории"] + all_categories)
        with f_col2:
            status_filter = st.radio("Статус", ["Все", "Разблокированные", "Закрытые"], horizontal=True)

        filtered_list = synced_achievements
        if selected_cat != "Все категории":
            filtered_list = [a for a in filtered_list if a["category"] == selected_cat]
        if status_filter == "Разблокированные":
            filtered_list = [a for a in filtered_list if a["unlocked"]]
        elif status_filter == "Закрытые":
            filtered_list = [a for a in filtered_list if not a["unlocked"]]

        st.caption(f"Отображено трофеев: {len(filtered_list)}")

        ach_cols = st.columns(2)
        for idx, ach in enumerate(filtered_list):
            is_unl = ach["unlocked"]
            card_cls = "trophy-card trophy-unlocked" if is_unl else "trophy-card"
            icon_disp = ach["icon"] if is_unl else "🔒"
            date_badge = f"Открыто: {ach['date']}" if is_unl else "В процессе"

            with ach_cols[idx % 2]:
                st.markdown(f"""
                <div class="{card_cls}">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <div style="font-weight:700; font-size:0.95rem;">
                                {icon_disp} {ach['title']}
                            </div>
                            <div style="font-size:0.78rem; color:#8b949e; margin-top:4px;">
                                {ach['desc']}
                            </div>
                        </div>
                        <span class="pill-badge">{ach['code']}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:8px; font-size:0.72rem; color:#8b949e;">
                        <span>{ach['category']}</span>
                        <span style="color:{accent_col if is_unl else '#8b949e'}; font-weight:600;">{date_badge}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Подвкладка 2: Цели на месяц и год из database.py
    with g_tab2:
        st.markdown("##### 🎯 Цели на месяц и год")
        df_goals = DatabaseManager.get_goals(user_id)

        if not df_goals.empty:
            for _, row in df_goals.iterrows():
                g_id = int(row["id"])
                g_period = "📅 Месяц" if row["goal_period"] == "month" else "🚀 Год"
                g_title = row["goal_title"]
                g_target = float(row["target_value"])
                g_curr = float(row["current_value"])
                g_unit = row["unit"]
                pct = min(1.0, max(0.0, g_curr / g_target)) if g_target > 0 else 0.0

                st.markdown(f"**{g_period}: {g_title}** ({g_curr:.0f} / {g_target:.0f} {g_unit})")
                st.progress(pct)

                gc1, gc2 = st.columns([3, 1])
                with gc1:
                    new_val = st.number_input(
                        f"Обновить прогресс ({g_title})",
                        min_value=0.0,
                        max_value=g_target * 2.0,
                        value=g_curr,
                        step=1.0,
                        key=f"goal_in_{g_id}",
                        label_visibility="collapsed"
                    )
                with gc2:
                    if st.button("Сохранить", key=f"goal_btn_{g_id}", use_container_width=True):
                        DatabaseManager.update_goal_progress(g_id, new_val)
                        st.rerun()
                st.divider()

    # Подвкладка 3: Таблица лидеров из database.py
    with g_tab3:
        st.markdown("##### 🌐 Рейтинг операторов NeuroGuard")
        df_lb = DatabaseManager.get_leaderboard()
        st.dataframe(df_lb, use_container_width=True, hide_index=True)


# ------------------------------------------------------------------------------
# ВКЛАДКА 6: БАЗА ЗНАНИЙ И БИБЛИОТЕКА (40 КНИГ ИЗ LIBRARY_DATA.PY)
# ------------------------------------------------------------------------------
with tabs[5]:
    st.markdown("#### 📚 Интеллектуальная база знаний (40 фундаментальных книг)")
    st.caption("Структурированный каталог литературы по мышлению, биохакингу ЦНС, алгоритмам и спортивной дисциплине.")

    lib_col1, lib_col2 = st.columns([1.2, 1])
    with lib_col1:
        lib_section = st.selectbox("Раздел библиотеки", ["Все разделы"] + list(LIBRARY_CATALOG.keys()))
    with lib_col2:
        status_book_filter = st.selectbox("Статус чтения", ["Все статусы", "Прочитано", "В процессе", "В планах"])

    books_to_show = []
    for sec_name, book_list in LIBRARY_CATALOG.items():
        if lib_section != "Все разделы" and sec_name != lib_section:
            continue
        for b in book_list:
            if status_book_filter != "Все статусы" and b["status"] != status_book_filter:
                continue
            b_copy = b.copy()
            b_copy["section"] = sec_name
            books_to_show.append(b_copy)

    st.caption(f"Найдено книг в каталоге: {len(books_to_show)}")

    b_cols = st.columns(2)
    for idx, book in enumerate(books_to_show):
        status_color = "#3fb950" if book["status"] == "Прочитано" else ("#58a6ff" if book["status"] == "В процессе" else "#8b949e")
        with b_cols[idx % 2]:
            st.markdown(f"""
            <div class="linear-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-weight:700; font-size:0.98rem;">📖 {book['title']}</div>
                        <div style="font-size:0.8rem; color:#8b949e; margin-top:2px;">Автор: <b>{book['author']}</b> • {book['section']}</div>
                    </div>
                    <span class="pill-badge" style="color:{status_color}; border-color:{status_color};">{book['status']}</span>
                </div>
                <div style="font-size:0.84rem; color:#c9d1d9; margin-top:10px; line-height:1.45;">
                    {book['desc']}
                </div>
            </div>
            """, unsafe_allow_html=True)
