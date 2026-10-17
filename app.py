import os
import time
from datetime import date
import streamlit as st
import pandas as pd

# ==============================================================================
# МОДУЛЬНЫЕ ИМПОРТЫ ИЗ ФАЙЛОВ ПРОЕКТА
# ==============================================================================
from database import DatabaseManager
from engine import CoreEngine
from achievements_data import ACHIEVEMENTS_CATALOG
from library_data import SKINS_CATALOG, WORKOUT_PROTOCOLS, LIBRARY_CATALOG

# ==============================================================================
# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ И ИНИЦИАЛИЗАЦИЯ БАЗЫ
# ==============================================================================
st.set_page_config(
    page_title="NeuroGuard OS — Модульная система биохакинга и продуктивности",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

DatabaseManager.init_db()

# ==============================================================================
# 2. СОХРАНЕНИЕ СЕССИИ И СОСТОЯНИЙ (SESSION STATE)
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

# Оперативные био-счетчики реального времени (Трекеры ЦНС и зрения)
if "water_ml" not in st.session_state:
    st.session_state.water_ml = 1000
if "eye_breaks_count" not in st.session_state:
    st.session_state.eye_breaks_count = 3
if "caffeine_mg" not in st.session_state:
    st.session_state.caffeine_mg = 0
if "resting_hr" not in st.session_state:
    st.session_state.resting_hr = 60
if "no_impact_streak" not in st.session_state:
    st.session_state.no_impact_streak = 7

# Чек-лист ежедневной дисциплины
if "habits" not in st.session_state:
    st.session_state.habits = {
        "Гидратация: выпить норму чистой воды (2500 мл)": False,
        "Зрение: минимум 5 циклов разгрузки глаз (20-20-20)": False,
        "Глубокий фокус: 90 минут кода / профильных задач без телефона": False,
        "Физическая база: суставная разминка / ОФП / статика": False,
        "Интеллект: чтение 30+ страниц профильной литературы": False,
        "Гигиена сна: отключение экранов за 60 минут до отбоя": False
    }

# Личные рекорды (PR)
if "pr_records" not in st.session_state:
    st.session_state.pr_records = {
        "Подтягивания за 14 мин (повторений)": 100.0,
        "Закрытый горизонт (секунд)": 15.0,
        "Жим штанги лежа (кг)": 100.0,
        "Бег 5 км (минут)": 21.5,
        "Свободный вис на перекладине (сек)": 120.0,
        "Решено задач информатики/ЕГЭ за день": 25.0
    }

# ==============================================================================
# 3. ДИНАМИЧЕСКАЯ СТИЛИЗАЦИЯ (LINEAR / NOTION ULTRA-CLEAN UI)
# ==============================================================================
skin_key = st.session_state.active_skin
if skin_key not in SKINS_CATALOG:
    skin_key = "cyber_blue"

current_skin = SKINS_CATALOG[skin_key]
accent_col = current_skin["accent"]
glow_col = current_skin["glow"]

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #0d1117;
        color: #e6edf3;
    }}

    /* Убираем системные стрелочки в экспандерах */
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
        box-shadow: 0 4px 22px {glow_col};
    }}

    /* Карточки витрины лендинга */
    .landing-feature-card {{
        background: linear-gradient(165deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #30363d;
        border-top: 3px solid {accent_col};
        border-radius: 12px;
        padding: 16px 18px;
        margin-top: 8px;
        margin-bottom: 18px;
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
        font-size: 0.75rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.06em;
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

    /* Карточки трофеев */
    .trophy-card {{
        background: #12161c;
        border: 1px solid #21262d;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        opacity: 0.5;
    }}
    .trophy-unlocked {{
        background: #161b22;
        border: 1px solid {accent_col};
        box-shadow: 0 0 14px {glow_col};
        opacity: 1.0;
    }}

    /* Прогресс-бары */
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


def render_image_safe(filename: str):
    """Безопасный вывод изображений из корня репозитория"""
    if os.path.exists(filename):
        st.image(filename, use_container_width=True)


# ==============================================================================
# 4. ПЕРВОНАЧАЛЬНЫЙ ЭКРАН-ЛЕНДИНГ С КАРТИНКАМИ И ПРЕИМУЩЕСТВАМИ (ДО ВХОДА)
# ==============================================================================
if st.session_state.user is None:
    # Главный баннер hero.jpg
    render_image_safe("hero.jpg")

    st.markdown("""
    <div style="text-align: center; padding: 14px 0 24px 0;">
        <span class="pill-badge">NEUROGUARD OS • SYSTEM RELEASE 2.5</span>
        <h1 style="margin-top: 10px; font-size: 2.4rem; font-weight: 800; letter-spacing: -0.02em;">
            Операционная система управления ресурсом ЦНС, спортом и интеллектом
        </h1>
        <p style="color: #8b949e; font-size: 1.05rem; max-width: 780px; margin: 0 auto;">
            Персональная аналитическая платформа на стыке медицины зрения, кибернетического трекинга нагрузки,
            калистеники, единоборств и подготовки к сложнейшим алгоритмическим вызовам.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Блок авторизации на видном месте
    auth_c1, auth_c2 = st.columns([1.25, 1])
    with auth_c1:
        st.markdown("""
        <div class="linear-card" style="height: 100%;">
            <h4 style="margin-top: 0;">⚡ Почему NeuroGuard OS?</h4>
            <p style="font-size: 0.9rem; color: #c9d1d9; line-height: 1.6;">
                Обычные трекеры задач не учитывают биологическую цену успеха. <b>NeuroGuard OS</b> связывает твой
                когнитивный объем (код, математика, ЕГЭ, олимпиады) и жесткие физические тренировки с реальным состоянием
                центральной нервной системы и безопасностью сетчатки глаз.
            </p>
            <div style="margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap;">
                <span class="pill-badge">🛡️ Предиктивный анализ выгорания</span>
                <span class="pill-badge">👁️ Защита зрения и ВЧД</span>
                <span class="pill-badge">⚔️ RPG-прокачка 4 характеристик</span>
                <span class="pill-badge">🏆 100 эпических трофеев</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Мгновенный вход: Профиль Основателя (Igor_Founder)", type="primary", use_container_width=True):
            user_obj, _ = DatabaseManager.authenticate_or_register("Igor_Founder", "0000", create_new=False)
            if user_obj:
                st.session_state.user = user_obj
                st.query_params["u"] = "Igor_Founder"
                st.query_params["p"] = "0000"
                st.rerun()

    with auth_c2:
        st.markdown('<div class="linear-card">', unsafe_allow_html=True)
        auth_mode = st.radio("Режим авторизации", ["Вход в аккаунт", "Регистрация нового оператора"], horizontal=True)
        u_input = st.text_input("Никнейм оператора", value="Igor_Founder")
        p_input = st.text_input("PIN-код доступа", value="0000", type="password")

        if st.button("Открыть рабочее пространство", use_container_width=True):
            is_new = (auth_mode == "Регистрация нового оператора")
            user_obj, err = DatabaseManager.authenticate_or_register(u_input, p_input, create_new=is_new)
            if err:
                st.error(err)
            else:
                st.session_state.user = user_obj
                st.query_params["u"] = u_input
                st.query_params["p"] = p_input
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ВИТРИНА ПРЕИМУЩЕСТВ С КАРТИНКАМИ ИЗ РЕПОЗИТОРИЯ (bio.jpg, rpg.jpg, reset.jpg, trophies.jpg)
    st.markdown("### 🔬 Архитектура и ключевые преимущества экосистемы")
    st.caption("Все модули интегрированы в единое ядро с автоматическим расчетом метрик и синхронизацией базы данных.")

    feat_col1, feat_col2 = st.columns(2)

    with feat_col1:
        render_image_safe("bio.jpg")
        st.markdown("""
        <div class="landing-feature-card">
            <span class="pill-badge">МОДУЛЬ 01 • БИОМЕТРИЯ И ЗРЕНИЕ</span>
            <h4 style="margin: 8px 0 6px 0;">🛡️ Защита сетчатки и индекс готовности ЦНС (Readiness)</h4>
            <p style="font-size: 0.88rem; color: #8b949e; line-height: 1.5; margin-bottom: 0;">
                Ежедневный мониторинг качества сна, экранного времени, спазма аккомодации и ударной нагрузки.
                Встроенные счетчики гидратации, циклов 20-20-20 и умный медицинский советник, блокирующий опасные
                процедуры (например, сауну или натуживание) при риске повышения внутричерепного давления.
            </p>
        </div>
        """, unsafe_allow_html=True)

        render_image_safe("reset.jpg")
        st.markdown("""
        <div class="landing-feature-card">
            <span class="pill-badge">МОДУЛЬ 03 • ПРОТОКОЛЫ И НЕЙРО-РЕЗЕТ</span>
            <h4 style="margin: 8px 0 6px 0;">🧘 Профессиональные циклы тренировок и перезагрузка ЦНС</h4>
            <p style="font-size: 0.88rem; color: #8b949e; line-height: 1.5; margin-bottom: 0;">
                Структурированные программы по калистенике (выход на горизонт, 100 подтягиваний), единоборствам
                (каратэ, кобудо, самбо), силовому жиму и подготовке к восхождениям. Интерактивный секундомер и
                протоколы быстрого снятия стресса через дыхание и пальминг.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with feat_col2:
        render_image_safe("rpg.jpg")
        st.markdown("""
        <div class="landing-feature-card">
            <span class="pill-badge">МОДУЛЬ 02 • ГЕЙМИФИКАЦИЯ И ПРОДУКТИВНОСТЬ</span>
            <h4 style="margin: 8px 0 6px 0;">⚔️ Оцифровка реальных навыков в RPG-характеристики</h4>
            <p style="font-size: 0.88rem; color: #8b949e; line-height: 1.5; margin-bottom: 0;">
                Каждое силовое повторение, раунд боя с тенью, решенная задача на Python и прочитанная страница
                конвертируются в очки Силы (STR), Ловкости (AGI), Интеллекта (INT) и Дисциплины (DSC). Повышай уровень
                и открывай эксклюзивные кибер-скины оформления.
            </p>
        </div>
        """, unsafe_allow_html=True)

        render_image_safe("trophies.jpg")
        st.markdown("""
        <div class="landing-feature-card">
            <span class="pill-badge">МОДУЛЬ 04 • ЗАЛ СЛАВЫ И БАЗА ЗНАНИЙ</span>
            <h4 style="margin: 8px 0 6px 0;">🏆 100 достижений, стратегические цели и 40 книг</h4>
            <p style="font-size: 0.88rem; color: #8b949e; line-height: 1.5; margin-bottom: 0;">
                Автоматическая проверка триггеров по 8 категориям: от олимпиад и стартапов до экстремальных рекордов.
                Включает трекинг месячных/годовых целей, глобальную таблицу лидеров и отборную библиотеку из 40 лучших
                книг по алгоритмам, мышлению и биохакингу.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.stop()


# ==============================================================================
# 5. ЗАГРУЗКА ДАННЫХ АВТОРИЗОВАННОГО ОПЕРАТОРА И СИНХРОНИЗАЦИЯ ЯДРА
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

# Вычисляем суммарные характеристики персонажа
sum_str = int(df_rpg["str_pts"].sum()) if not df_rpg.empty else 0
sum_agi = int(df_rpg["agi_pts"].sum()) if not df_rpg.empty else 0
sum_int = int(df_rpg["int_pts"].sum()) if not df_rpg.empty else 0
sum_dsc = int(df_rpg["dsc_pts"].sum()) if not df_rpg.empty else 0

# Авто-синхронизация всех 100 достижений через CoreEngine
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
# 6. БОКОВАЯ ПАНЕЛЬ: КАРТОЧКА ПЕРСОНАЖА, СКИНЫ, ЭКСПОРТ
# ==============================================================================
with st.sidebar:
    st.markdown(f"""
    <div class="linear-card" style="padding: 16px;">
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <div style="font-size: 2.0rem;">{current_skin['avatar']}</div>
            <span class="pill-badge">{'💎 PRO STATUS' if is_pro else 'FREE TIER'}</span>
        </div>
        <div style="font-weight: 700; font-size: 1.15rem; margin-top: 8px;">{username}</div>
        <div style="font-size: 0.8rem; color: #8b949e;">
            {current_skin['role']} • <span style="color:{rank_color}; font-weight:700;">{rank_title}</span>
        </div>
        <div style="margin-top: 12px; font-size: 0.78rem; display:flex; justify-content:space-between;">
            <span>Уровень {user_lvl}</span>
            <span style="color:{accent_col}; font-weight:600;">{total_xp} XP ({xp_in_curr_lvl}/500)</span>
        </div>
        <div class="xp-bar-bg">
            <div class="xp-bar-fill" style="width: {xp_progress_pct}%;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size: 0.75rem; color: #8b949e; margin-top: 6px;">
            <span>Трофеи: <b>{unlocked_count}/100</b></span>
            <span>ЦНС: <b>{last_readiness}%</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### 🎨 Скин и визуальный профиль")
    skin_options = list(SKINS_CATALOG.keys())
    selected_skin = st.selectbox(
        "Выбор темы интерфейса",
        options=skin_options,
        index=skin_options.index(skin_key),
        format_func=lambda k: f"{SKINS_CATALOG[k]['avatar']} {SKINS_CATALOG[k]['name']} (LVL {SKINS_CATALOG[k]['min_lvl']}+)",
        label_visibility="collapsed"
    )

    if selected_skin != skin_key:
        req_lvl = SKINS_CATALOG[selected_skin]["min_lvl"]
        if user_lvl >= req_lvl or is_pro:
            st.session_state.active_skin = selected_skin
            st.rerun()
        else:
            st.warning(f"Требуется Уровень {req_lvl} или PRO-аккаунт.")

    st.caption(SKINS_CATALOG[skin_key]["desc"])
    st.divider()

    # Быстрая сводка статов в сайдбаре
    st.markdown("##### ⚡ Матрица характеристик")
    sc_col1, sc_col2 = st.columns(2)
    sc_col1.metric("🦾 STR", sum_str)
    sc_col2.metric("⚡ AGI", sum_agi)
    sc_col1.metric("🧠 INT", sum_int)
    sc_col2.metric("👑 DSC", sum_dsc)

    st.divider()

    # PRO переключатель
    pro_toggle = st.toggle("💎 Активировать PRO (+25% XP)", value=is_pro)
    if pro_toggle != is_pro:
        DatabaseManager.set_pro_status(user_id, pro_toggle)
        st.session_state.user["is_pro"] = pro_toggle
        st.rerun()

    # Экспорт данных в один клик (TXT + CSV)
    st.markdown("##### 📥 Экспорт данных в 1 клик")
    report_text = CoreEngine.generate_weekly_report(username, is_pro, df_health, df_rpg)
    st.download_button(
        label="📄 Скачать официальный отчёт (TXT)",
        data=report_text.encode("utf-8"),
        file_name=f"neuroguard_report_{date.today()}.txt",
        mime="text/plain",
        use_container_width=True
    )

    if not df_rpg.empty:
        csv_rpg = df_rpg.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📊 Выгрузить базу логов (CSV)",
            data=csv_rpg,
            file_name=f"neuroguard_rpg_logs_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )

    if st.button("🚪 Выйти из системы (На Лендинг)", use_container_width=True):
        st.session_state.user = None
        st.query_params.clear()
        st.rerun()


# ==============================================================================
# 7. ОСНОВНЫЕ РАБОЧИЕ ВКЛАДКИ (БЕЗ ЛИШНИХ БАННЕРОВ, ЧИСТЫЙ ФУНКЦИОНАЛ)
# ==============================================================================
tabs = st.tabs([
    "🧭 Командный Центр",
    "🛡️ Биометрия & Трекер ЦНС",
    "⚔️ Продуктивность & RPG",
    "🧘 Протоколы, Резет & Таймер",
    "🏆 Зал Славы (100) & Цели",
    "📚 База Знаний (40 книг)"
])


# ------------------------------------------------------------------------------
# ВКЛАДКА 1: КОМАНДНЫЙ ЦЕНТР (ДАШБОРД, УТРЕННЯЯ ДЕКЛАРАЦИЯ, ПРИВЫЧКИ, PR)
# ------------------------------------------------------------------------------
with tabs[0]:
    # Верхняя панель оперативных метрик
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Готовность ЦНС (Readiness)</div>
            <div class="metric-value">{last_readiness}%</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Ранг и Уровень</div>
            <div class="metric-value">LVL {user_lvl} <span style="font-size:0.9rem; color:{rank_color};">{rank_title}</span></div>
        </div>
        """, unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Открыто Трофеев</div>
            <div class="metric-value">{unlocked_count} <span style="font-size:0.95rem; color:#8b949e;">/ 100</span></div>
        </div>
        """, unsafe_allow_html=True)
    with m_col4:
        st.markdown(f"""
        <div class="metric-box" style="border-left-color: {burnout_info['color']};">
            <div class="metric-label">Нейро-баланс / Выгорание</div>
            <div class="metric-value" style="font-size: 1.0rem; color: {burnout_info['color']}; margin-top: 10px;">
                {burnout_info['risk_level']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Предиктивный блок выгорания
    st.markdown(f"""
    <div class="linear-card" style="border-left: 4px solid {burnout_info['color']};">
        <div style="font-weight: 600; margin-bottom: 4px;">🤖 Предиктивная диагностика ядра</div>
        <div style="font-size: 0.9rem; color: #c9d1d9;">{burnout_info['message']}</div>
    </div>
    """, unsafe_allow_html=True)

    col_d1, col_d2 = st.columns([1.15, 1])

    with col_d1:
        # Утреннее окно декларации намерений
        st.markdown("##### 🎯 Утренняя декларация намерений")
        st.caption("Зафиксируй главную цель дня. Фокус не должен распыляться.")

        intent_val = st.text_input(
            "Главный вектор дня",
            value=st.session_state.morning_intent,
            placeholder="Например: Закрыть 15 задач по Python/ЕГЭ, сделать 100 подтягиваний и удержать спазм глаз ≤ 3",
            label_visibility="collapsed"
        )
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("📌 Зафиксировать декларацию", type="primary", use_container_width=True):
                st.session_state.morning_intent = intent_val
                st.session_state.intent_locked = True
        with c_btn2:
            if st.button("🔄 Очистить вектор", use_container_width=True):
                st.session_state.morning_intent = ""
                st.session_state.intent_locked = False
                st.rerun()

        if st.session_state.intent_locked and st.session_state.morning_intent:
            st.markdown(f"""
            <div class="linear-card" style="border-color: {accent_col}; margin-top: 10px;">
                <span class="pill-badge">ВЕКТОР ЗАФИКСИРОВАН</span>
                <div style="font-weight: 700; font-size: 1.05rem; margin-top: 8px;">«{st.session_state.morning_intent}»</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Доска личных рекордов (PR)
        st.markdown("##### 🏆 Доска личных рекордов и нормативов (PR)")
        st.caption("Актуализируй свои пиковые силовые и функциональные показатели.")
        pr_cols = st.columns(2)
        for idx, (pr_name, pr_val) in enumerate(st.session_state.pr_records.items()):
            with pr_cols[idx % 2]:
                new_pr = st.number_input(pr_name, value=float(pr_val), step=1.0, key=f"pr_{idx}")
                st.session_state.pr_records[pr_name] = new_pr

    with col_d2:
        # Трекер ежедневных привычек
        st.markdown("##### ✅ Чек-лист ежедневной дисциплины")
        st.caption("Отмечай выполненные стандарты дня для сохранения высокого тонуса.")

        completed_habits = 0
        for h_name in list(st.session_state.habits.keys()):
            st.session_state.habits[h_name] = st.checkbox(h_name, value=st.session_state.habits[h_name])
            if st.session_state.habits[h_name]:
                completed_habits += 1

        habit_pct = int((completed_habits / len(st.session_state.habits)) * 100)
        st.progress(habit_pct / 100.0, text=f"Индекс соблюдения режима: {habit_pct}% ({completed_habits}/{len(st.session_state.habits)})")

        st.divider()

        # Оперативная сводка био-счетчиков на главном экране
        st.markdown("##### 🔋 Оперативные био-счетчики сегодня")
        q_c1, q_c2, q_c3 = st.columns(3)
        q_c1.metric("💧 Гидратация", f"{st.session_state.water_ml} мл", "Норма 2500 мл")
        q_c2.metric("👁️ Разгрузка глаз", f"{st.session_state.eye_breaks_count} цикл.", "Протокол 20-20-20")
        q_c3.metric("🛡️ Без ударов в голову", f"{st.session_state.no_impact_streak} дн.", "Защита сетчатки")


# ------------------------------------------------------------------------------
# ВКЛАДКА 2: БИОМЕТРИЯ, ЗРЕНИЕ И ОПЕРАТИВНЫЙ ТРЕКЕР-СЧЕТЧИК ЦНС
# ------------------------------------------------------------------------------
with tabs[1]:
    st.markdown("#### 🛡️ Биометрия, защита зрения и оперативный трекер ЦНС")
    st.caption("Полноценный пульт контроля физиологического ресурса, спазма аккомодации и восстановления.")

    # 1. БЛОК ИНТЕРАКТИВНЫХ ОПЕРАТИВНЫХ СЧЕТЧИКОВ (ТОТ САМЫЙ ТРЕКЕР-СЧЕТЧИК БИО И ЦНС)
    st.markdown("##### ⚡ Оперативные счетчики био-режима (Live Counters)")
    cnt_col1, cnt_col2, cnt_col3, cnt_col4 = st.columns(4)

    with cnt_col1:
        st.markdown('<div class="linear-card">', unsafe_allow_html=True)
        st.markdown("**💧 Трекер гидратации**")
        st.markdown(f"<h3 style='margin:4px 0; color:{accent_col};'>{st.session_state.water_ml} / 2500 мл</h3>", unsafe_allow_html=True)
        st.progress(min(1.0, st.session_state.water_ml / 2500.0))
        wc1, wc2 = st.columns(2)
        if wc1.button("+250 мл", key="w_add", use_container_width=True):
            st.session_state.water_ml += 250
            st.rerun()
        if wc2.button("Сброс", key="w_res", use_container_width=True):
            st.session_state.water_ml = 0
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with cnt_col2:
        st.markdown('<div class="linear-card">', unsafe_allow_html=True)
        st.markdown("**👁️ Циклы 20-20-20 (Зрение)**")
        st.markdown(f"<h3 style='margin:4px 0; color:{accent_col};'>{st.session_state.eye_breaks_count} / 8 разгрузок</h3>", unsafe_allow_html=True)
        st.progress(min(1.0, st.session_state.eye_breaks_count / 8.0))
        ec1, ec2 = st.columns(2)
        if ec1.button("+1 цикл", key="e_add", use_container_width=True):
            st.session_state.eye_breaks_count += 1
            st.rerun()
        if ec2.button("Сброс", key="e_res", use_container_width=True):
            st.session_state.eye_breaks_count = 0
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with cnt_col3:
        st.markdown('<div class="linear-card">', unsafe_allow_html=True)
        st.markdown("**☕ Кофеин / Стимуляторы ЦНС**")
        caff_color = "#3fb950" if st.session_state.caffeine_mg <= 150 else ("#d29922" if st.session_state.caffeine_mg <= 300 else "#f85149")
        st.markdown(f"<h3 style='margin:4px 0; color:{caff_color};'>{st.session_state.caffeine_mg} мг</h3>", unsafe_allow_html=True)
        st.caption("Безопасный лимит для ЦНС: ≤ 200 мг")
        cc1, cc2 = st.columns(2)
        if cc1.button("+80 мг", key="c_add", use_container_width=True):
            st.session_state.caffeine_mg += 80
            st.rerun()
        if cc2.button("0 мг", key="c_res", use_container_width=True):
            st.session_state.caffeine_mg = 0
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with cnt_col4:
        st.markdown('<div class="linear-card">', unsafe_allow_html=True)
        st.markdown("**❤️ ЧСС покоя и серия защиты**")
        st.session_state.resting_hr = st.number_input("Утренний пульс (уд/мин)", 40, 120, int(st.session_state.resting_hr), step=1)
        hr_status = "Отличное восстановление" if st.session_state.resting_hr <= 62 else "Повышенный тонус симпатики"
        st.caption(f"Статус: {hr_status}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # 2. ОСНОВНАЯ ФОРМА РАСЧЕТА READINESS И ПРОТОКОЛ ВОССТАНОВЛЕНИЯ
    b_col1, b_col2 = st.columns([1.15, 1])

    with b_col1:
        st.markdown("##### 📋 Ввод параметров дня и живой калькулятор Readiness")
        log_d = st.date_input("Дата записи в био-базу", value=date.today())

        c_sl1, c_sl2 = st.columns(2)
        with c_sl1:
            sleep_h = st.slider("Продолжительность сна (ч)", 3.0, 12.0, 8.0, 0.5)
            study_h = st.slider("Экранное время / Код и учёба (ч)", 0.0, 16.0, 5.0, 0.5)
        with c_sl2:
            sleep_q = st.slider("Качество и глубина сна (1–10)", 1, 10, 8)
            eye_strain = st.slider("Спазм и усталость глаз (1–10)", 1, 10, 3)

        train_type = st.selectbox(
            "Тип физической нагрузки сегодня",
            [
                "Отдых / Активное восстановление",
                "ОФП и Калистеника (Турники / Брусья / Горизонт)",
                "Техника боевых искусств / Ката / Кобудо / Бой с тенью",
                "Силовая тренировка с железом",
                "Спарринги / Борьба / Соревновательная нагрузка",
                "Кардио / Бег / Выносливость"
            ]
        )
        train_int = st.slider("Интенсивность тренировки (0–10)", 0, 10, 5)
        head_impact = st.checkbox("⚠️ Была ударная нагрузка на голову или предельное натуживание (ВЧД)")

        # Живой предпросмотр индекса Readiness ДО сохранения
        live_readiness = CoreEngine.calculate_readiness(
            sleep_h=sleep_h,
            sleep_q=sleep_q,
            study_h=study_h,
            eye_strain=eye_strain,
            train_int=train_int,
            head_impact=head_impact
        )
        live_rank, live_col = CoreEngine.get_rank_badge(live_readiness)

        st.markdown(f"""
        <div class="linear-card" style="border-left: 4px solid {live_col};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:0.78rem; color:#8b949e; text-transform:uppercase;">Расчетный индекс готовности ЦНС</div>
                    <div style="font-size:1.45rem; font-weight:800; color:{live_col};">{live_readiness}% — {live_rank}</div>
                </div>
                <span class="pill-badge">LIVE PREVIEW</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("💾 Зафиксировать био-статус в базу данных", type="primary", use_container_width=True):
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
                live_readiness, advice_str
            ))
            st.success(f"Запись за {log_d} сохранена в БД! Индекс готовности: {live_readiness}%")
            st.rerun()

    with b_col2:
        st.markdown("##### 🤖 Медицинский и восстановительный советник (AI Engine)")
        rec_advice = CoreEngine.generate_recovery_advice(df_health)
        st.info(rec_advice)

        # Чек-лист безопасности сетчатки и сосудов
        with st.expander("👁️ Протокол офтальмологической и сосудистой безопасности", expanded=True):
            st.checkbox("Освещение рабочего стола без бликов и мерцания (ШИМ)")
            st.checkbox("Дистанция до монитора 60–70 см, верхний край на уровне глаз")
            st.checkbox("Исключены задержки дыхания на усилии (профилактика скачков ВЧД)")
            st.checkbox("Выполнено расслабление подзатылочных мышц шеи")

        if not df_health.empty:
            st.markdown("##### 📈 График динамики готовности ЦНС и сна")
            chart_df = df_health[["log_date", "readiness_score", "sleep_hours", "eye_strain"]].sort_values("log_date").set_index("log_date")
            st.line_chart(chart_df[["readiness_score"]])

            st.markdown("##### 🗂️ Последние записи био-мониторинга")
            st.dataframe(
                df_health[["log_date", "sleep_hours", "study_hours", "eye_strain", "training_type", "readiness_score"]].head(7),
                use_container_width=True,
                hide_index=True
            )


# ------------------------------------------------------------------------------
# ВКЛАДКА 3: ПРОДУКТИВНОСТЬ, УЧЁБА, ТРЕНИРОВКИ & RPG-ДВИЖОК
# ------------------------------------------------------------------------------
with tabs[2]:
    st.markdown("#### ⚔️ Оцифровка продуктивности, кодинга и тренировочного объёма")
    st.caption("Каждое полезное действие за день пересчитывается через `CoreEngine` в опыт (XP) и очки 4 базовых характеристик.")

    r_col1, r_col2 = st.columns([1.15, 1])

    with r_col1:
        st.markdown("##### 📝 Отчёт за день и калькулятор начисления опыта")
        rpg_date = st.date_input("Дата отчёта", value=date.today(), key="rpg_d")

        rc1, rc2 = st.columns(2)
        with rc1:
            ex_reps = st.number_input("💪 Силовые повторения (подтягивания, отжимания, зал)", 0, 3000, 100, step=10)
            agi_drills = st.number_input("🥋 Раунды техники / ката / кобудо / бой с тенью", 0, 50, 5, step=1)
            pages = st.number_input("📖 Прочитано страниц профильных книг", 0, 500, 30, step=5)
        with rc2:
            tasks = st.number_input("💻 Решено задач (Python / ЕГЭ / Олимпиады)", 0, 200, 10, step=1)
            topics = st.number_input("🧠 Освоено новых тем / алгоритмов / концептов", 0, 30, 2, step=1)
            plan_pct = st.slider("🎯 Процент выполнения плана дня (%)", 0, 100, 90, step=5)

        plan_text = st.text_input(
            "Краткий список закрытых квестов дня",
            placeholder="Например: Разобрал динамическое программирование, сделал 100 подтягиваний, дизайн 2 карточек..."
        )
        daily_note = st.text_area(
            "📓 Заметка в Хроники (рефлексия, идеи, состояние)",
            placeholder="Запиши ключевой инсайт дня — это также открывает достижения ветки 'Летописец Пути'..."
        )

        # Живой предпросмотр начисляемых RPG-очков
        p_str, p_agi, p_int, p_dsc, p_tot, p_xp = CoreEngine.calculate_rpg_stats(
            ex_reps=ex_reps,
            agi_drills=agi_drills,
            pages=pages,
            topics=topics,
            tasks=tasks,
            plan_pct=plan_pct,
            is_pro=is_pro
        )

        st.markdown(f"""
        <div class="linear-card" style="border-left: 4px solid {accent_col};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:0.78rem; color:#8b949e;">РАСЧЁТ НАГРАДЫ ЗА СЕССИЮ ({'С УЧЕТОМ БОНУСА PRO +25%' if is_pro else 'БАЗОВЫЙ ТАРИФ'})</div>
                    <div style="font-size:1.35rem; font-weight:800; color:{accent_col};">+{p_xp} XP</div>
                    <div style="font-size:0.82rem; color:#c9d1d9; margin-top:4px;">
                        🦾 STR: <b>+{p_str}</b> &nbsp;|&nbsp; ⚡ AGI: <b>+{p_agi}</b> &nbsp;|&nbsp; 🧠 INT: <b>+{p_int}</b> &nbsp;|&nbsp; 👑 DSC: <b>+{p_dsc}</b>
                    </div>
                </div>
                <span class="pill-badge">Действий: {p_tot}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("⚡ Зафиксировать отчёт и начислить XP", type="primary", use_container_width=True):
            rpg_msg = f"Начислено +{p_xp} XP | STR +{p_str}, AGI +{p_agi}, INT +{p_int}, DSC +{p_dsc}"
            DatabaseManager.save_rpg_log((
                user_id, str(rpg_date), ex_reps, agi_drills, pages,
                topics, tasks, plan_text, plan_pct, p_tot,
                p_xp, p_str, p_agi, p_int, p_dsc, rpg_msg, daily_note
            ))
            st.success(f"Отчёт сохранён! {rpg_msg}")
            st.rerun()

    with r_col2:
        st.markdown("##### 📊 Профиль прокачки характеристик оператора")
        max_stat_ref = max(500, sum_str, sum_agi, sum_int, sum_dsc)

        st.markdown('<div class="linear-card">', unsafe_allow_html=True)
        st.markdown(f"**🦾 Сила и Калистеника (STR): {sum_str} очк.**")
        st.progress(min(1.0, sum_str / float(max_stat_ref)))

        st.markdown(f"**⚡ Ловкость и Боевые искусства (AGI): {sum_agi} очк.**")
        st.progress(min(1.0, sum_agi / float(max_stat_ref)))

        st.markdown(f"**🧠 Интеллект, Код и Наука (INT): {sum_int} очк.**")
        st.progress(min(1.0, sum_int / float(max_stat_ref)))

        st.markdown(f"**👑 Дисциплина и Выполнение плана (DSC): {sum_dsc} очк.**")
        st.progress(min(1.0, sum_dsc / float(max_stat_ref)))
        st.markdown('</div>', unsafe_allow_html=True)

        if not df_rpg.empty:
            st.markdown("##### 📈 График набора опыта (XP по дням)")
            xp_chart = df_rpg[["log_date", "xp_earned"]].sort_values("log_date").set_index("log_date")
            st.bar_chart(xp_chart)

            st.markdown("##### 📜 Хроники и заметки оператора")
            notes_df = df_rpg[df_rpg["daily_note"].fillna("") != ""][["log_date", "daily_note", "xp_earned"]].head(5)
            if not notes_df.empty:
                for _, nrow in notes_df.iterrows():
                    st.markdown(f"""
                    <div class="linear-card" style="padding:12px 16px;">
                        <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#8b949e;">
                            <span>📅 {nrow['log_date']}</span>
                            <span style="color:{accent_col}; font-weight:600;">+{nrow['xp_earned']} XP</span>
                        </div>
                        <div style="font-size:0.88rem; margin-top:6px;">{nrow['daily_note']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("Заметок пока нет. Оставь первую запись в поле рефлексии слева, чтобы открыть достижение 'Летописец Пути'!")


# ------------------------------------------------------------------------------
# ВКЛАДКА 4: ТРЕНИРОВОЧНЫЕ ПРОТОКОЛЫ, НЕЙРО-РЕЗЕТ ЦНС И ТАЙМЕР
# ------------------------------------------------------------------------------
with tabs[3]:
    st.markdown("#### 🧘 Протоколы тренировок, перезагрузка ЦНС и рабочий секундомер")
    st.caption("Структурированные тренировочные комплексы из `library_data.py` и быстрые протоколы снятия спазма глаз и стресса.")

    p_col1, p_col2 = st.columns([1.2, 1])

    with p_col1:
        st.markdown("##### 🥋 База тренировочных протоколов")
        selected_proto = st.selectbox("Выбери тренировочную программу", list(WORKOUT_PROTOCOLS.keys()))

        st.markdown('<div class="linear-card">', unsafe_allow_html=True)
        st.markdown(f"#### {selected_proto}")
        done_steps = 0
        steps_list = WORKOUT_PROTOCOLS[selected_proto]
        for idx, step_text in enumerate(steps_list, start=1):
            if st.checkbox(f"**Этап {idx}.** {step_text}", key=f"proto_{selected_proto}_{idx}"):
                done_steps += 1
        st.progress(done_steps / float(len(steps_list)), text=f"Выполнено этапов комплекса: {done_steps} из {len(steps_list)}")
        st.markdown('</div>', unsafe_allow_html=True)

        # Возвращенные протоколы быстрого нейро-резета ЦНС и зрения
        st.markdown("##### 🧬 Протоколы экспресс-резета ЦНС и зрения")
        res_tab1, res_tab2, res_tab3 = st.tabs([
            "👁️ Снятие спазма глаз (Пальминг)",
            "🌬️ Квадратное дыхание (4-4-4-4)",
            "⚡ Физиологический вздох (Анти-стресс)"
        ])
        with res_tab1:
            st.markdown("""
            <div class="linear-card">
                <b>Протокол глубокого расслабления цилиарной мышцы глаза:</b><br>
                1. Разотри ладони друг о друга до ощущения интенсивного тепла (10 сек).<br>
                2. Сложи ладони лодочкой и прикрой закрытые глаза без малейшего давления на глазные яблоки.<br>
                3. Убедись, что свет не проникает сквозь пальцы. Представь абсолютно черное пространство.<br>
                4. Сделай 10 медленных вдохов носом, расслабляя лоб, челюсть и затылок.<br>
                5. Посмотри вдаль в окно на самую удаленную точку на 20 секунд.
            </div>
            """, unsafe_allow_html=True)
        with res_tab2:
            st.markdown("""
            <div class="linear-card">
                <b>Тактическое дыхание для снижения кортизола и стабилизации пульса:</b><br>
                • <b>Вдох носом:</b> 4 секунды (плавно наполняя живот и грудную клетку).<br>
                • <b>Задержка на вдохе:</b> 4 секунды (без натуживания и спазма горла).<br>
                • <b>Плавный выдох:</b> 4 секунды.<br>
                • <b>Пауза на выдохе:</b> 4 секунды.<br>
                <i>Выполни 8–10 циклов по таймеру справа перед сложным экзаменом, кодингом или выходом на татами.</i>
            </div>
            """, unsafe_allow_html=True)
        with res_tab3:
            st.markdown("""
            <div class="linear-card">
                <b>Быстрое переключение в парасимпатический режим (метод Стэнфорда):</b><br>
                1. Сделай глубокий вдох через нос на 80% объема легких.<br>
                2. Без выдоха сделай резкий <b>второй до-вдох</b> носом до максимума (расправляет альвеолы).<br>
                3. Сделай максимально долгий и медленный выдох через рот (в 2 раза длиннее вдоха).<br>
                4. Повтори всего 3–5 раз — ЧСС снижается уже на 30-й секунде.
            </div>
            """, unsafe_allow_html=True)

    with p_col2:
        st.markdown("##### ⏱️ Интерактивный таймер / Секундомер сессий")
        st.caption("Для статики (закрытый горизонт, планка, вис), раундов боя с тенью, дыхания или пальминга.")

        timer_presets = {
            "🤸 Статика: Удержание горизонта / виса (15 сек)": 15,
            "🌬️ Дыхательный резет ЦНС (60 сек)": 60,
            "👁️ Пальминг и разгрузка зрения (90 сек)": 90,
            "🥋 Раунд боя с тенью / Кобудо (180 сек)": 180,
            "💻 Спринт глубокого фокуса (600 сек / 10 мин)": 600
        }
        chosen_preset = st.selectbox("Быстрый выбор пресета", list(timer_presets.keys()))
        seconds_to_run = st.number_input("Точное время (секунд)", min_value=5, max_value=1800, value=timer_presets[chosen_preset], step=5)

        if st.button("▶️ Запустить обратный отсчёт", type="primary", use_container_width=True):
            progress_bar = st.progress(0.0)
            status_txt = st.empty()
            for rem in range(int(seconds_to_run), 0, -1):
                pct = (seconds_to_run - rem) / float(seconds_to_run)
                progress_bar.progress(pct)
                mins, secs = divmod(rem, 60)
                status_txt.markdown(
                    f"""
                    <div class="linear-card" style="text-align:center; border-color:{accent_col};">
                        <div style="font-size:0.8rem; color:#8b949e;">АКТИВНАЯ СЕССИЯ</div>
                        <div style="font-size:2.4rem; font-weight:800; color:{accent_col};">{mins:02d}:{secs:02d}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                time.sleep(1)
            progress_bar.progress(1.0)
            status_txt.success("✅ Таймер завершён! Отличная работа.")


# ------------------------------------------------------------------------------
# ВКЛАДКА 5: ЗАЛ СЛАВЫ (ВСЕ 100 ДОСТИЖЕНИЙ), СТРАТЕГИЧЕСКИЕ ЦЕЛИ И ЛИДЕРБОРД
# ------------------------------------------------------------------------------
with tabs[4]:
    g_tab1, g_tab2, g_tab3 = st.tabs([
        f"🏆 Зал Славы ({unlocked_count}/100)",
        "🎯 Стратегические Цели (Месяц / Год)",
        "🌐 Глобальный Лидерборд"
    ])

    # Подвкладка 1: Полный каталог 100 ачивок из achievements_data.py
    with g_tab1:
        st.markdown("##### 🏆 Полный каталог 100 достижений NeuroGuard")
        st.progress(unlocked_count / 100.0, text=f"Общий прогресс Зала Славы: {unlocked_count}% ({unlocked_count} из 100 трофеев открыто)")

        all_categories = sorted(list(set(item["category"] for item in synced_achievements)))

        f_col1, f_col2, f_col3 = st.columns([1.2, 1, 1])
        with f_col1:
            selected_cat = st.selectbox("Фильтр по категории", ["Все категории (100)"] + all_categories)
        with f_col2:
            status_filter = st.selectbox("Статус трофеев", ["Все трофеи", "Только открытые", "Только закрытые"])
        with f_col3:
            search_ach = st.text_input("🔍 Поиск по названию или коду", placeholder="Например: Кобудо, ЕГЭ, BIO_01...")

        filtered_list = synced_achievements
        if selected_cat != "Все категории (100)":
            filtered_list = [a for a in filtered_list if a["category"] == selected_cat]
        if status_filter == "Только открытые":
            filtered_list = [a for a in filtered_list if a["unlocked"]]
        elif status_filter == "Только закрытые":
            filtered_list = [a for a in filtered_list if not a["unlocked"]]
        if search_ach.strip():
            q = search_ach.strip().lower()
            filtered_list = [
                a for a in filtered_list
                if q in a["title"].lower() or q in a["desc"].lower() or q in a["code"].lower()
            ]

        st.caption(f"Показано достижений: {len(filtered_list)}")

        ach_cols = st.columns(2)
        for idx, ach in enumerate(filtered_list):
            is_unl = ach["unlocked"]
            card_cls = "trophy-card trophy-unlocked" if is_unl else "trophy-card"
            icon_disp = ach["icon"] if is_unl else "🔒"
            date_badge = f"✅ Открыто: {ach['date']}" if is_unl else "⏳ В процессе"

            with ach_cols[idx % 2]:
                st.markdown(f"""
                <div class="{card_cls}">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <div style="font-weight:700; font-size:0.96rem;">
                                {icon_disp} {ach['title']}
                            </div>
                            <div style="font-size:0.8rem; color:#8b949e; margin-top:4px;">
                                {ach['desc']}
                            </div>
                        </div>
                        <span class="pill-badge">{ach['code']}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:10px; font-size:0.73rem; color:#8b949e;">
                        <span>{ach['category']}</span>
                        <span style="color:{accent_col if is_unl else '#8b949e'}; font-weight:600;">{date_badge}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Подвкладка 2: Стратегические цели на месяц и год
    with g_tab2:
        st.markdown("##### 🎯 Декомпозиция целей на Месяц и Год")
        df_goals = DatabaseManager.get_goals(user_id)

        if not df_goals.empty:
            for _, row in df_goals.iterrows():
                g_id = int(row["id"])
                g_period = "📅 МЕСЯЧНЫЙ РУБЕЖ" if row["goal_period"] == "month" else "🚀 ГОДОВАЯ СТРАТЕГИЯ"
                g_title = row["goal_title"]
                g_target = float(row["target_value"])
                g_curr = float(row["current_value"])
                g_unit = row["unit"]
                pct = min(1.0, max(0.0, g_curr / g_target)) if g_target > 0 else 0.0

                st.markdown(f"""
                <div class="linear-card" style="padding: 14px 18px; margin-bottom: 8px;">
                    <span class="pill-badge">{g_period}</span>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                        <div style="font-weight:700; font-size:1.0rem;">{g_title}</div>
                        <div style="font-weight:700; color:{accent_col};">{g_curr:.0f} / {g_target:.0f} {g_unit} ({pct*100:.0f}%)</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(pct)

                gc1, gc2 = st.columns([3, 1])
                with gc1:
                    new_val = st.number_input(
                        f"Значение ({g_title})",
                        min_value=0.0,
                        max_value=g_target * 2.0,
                        value=g_curr,
                        step=1.0,
                        key=f"goal_in_{g_id}",
                        label_visibility="collapsed"
                    )
                with gc2:
                    if st.button("Обновить прогресс", key=f"goal_btn_{g_id}", use_container_width=True):
                        DatabaseManager.update_goal_progress(g_id, new_val)
                        st.rerun()
                st.divider()

    # Подвкладка 3: Таблица лидеров
    with g_tab3:
        st.markdown("##### 🌐 Рейтинг операторов системы NeuroGuard")
        df_lb = DatabaseManager.get_leaderboard()
        st.dataframe(df_lb, use_container_width=True, hide_index=True)


# ------------------------------------------------------------------------------
# ВКЛАДКА 6: ИНТЕЛЛЕКТУАЛЬНАЯ БАЗА ЗНАНИЙ (40 КНИГ С ИНТЕРАКТИВНЫМ СТАТУСОМ)
# ------------------------------------------------------------------------------
with tabs[5]:
    st.markdown("#### 📚 Фундаментальная библиотека оператора (40 книг)")
    st.caption("Отборная литература по алгоритмам, когнитивной психологии, биохакингу ЦНС и спортивной дисциплине.")

    # Инициализация интерактивных статусов книг в сессии
    if "book_statuses" not in st.session_state:
        st.session_state.book_statuses = {
            b["title"]: b["status"]
            for sec in LIBRARY_CATALOG.values()
            for b in sec
        }

    # Сводка по библиотеке с учетом живых статусов
    all_books_flat = [b for sec in LIBRARY_CATALOG.values() for b in sec]
    read_cnt = sum(1 for b in all_books_flat if st.session_state.book_statuses.get(b["title"], b["status"]) == "Прочитано")
    proc_cnt = sum(1 for b in all_books_flat if st.session_state.book_statuses.get(b["title"], b["status"]) == "В процессе")
    plan_cnt = sum(1 for b in all_books_flat if st.session_state.book_statuses.get(b["title"], b["status"]) == "В планах")

    lb_m1, lb_m2, lb_m3 = st.columns(3)
    lb_m1.metric("✅ Прочитано полностью", f"{read_cnt} книг")
    lb_m2.metric("📖 В процессе изучения", f"{proc_cnt} книг")
    lb_m3.metric("📌 В очереди (В планах)", f"{plan_cnt} книг")

    lib_col1, lib_col2, lib_col3 = st.columns([1.2, 1, 1])
    with lib_col1:
        lib_section = st.selectbox("Раздел базы знаний", ["Все разделы"] + list(LIBRARY_CATALOG.keys()))
    with lib_col2:
        status_book_filter = st.selectbox("Статус чтения", ["Все статусы", "Прочитано", "В процессе", "В планах"])
    with lib_col3:
        book_search = st.text_input("🔍 Поиск книги или автора", placeholder="Например: Кормен, Гоггинс, Python...")

    books_to_show = []
    for sec_name, book_list in LIBRARY_CATALOG.items():
        if lib_section != "Все разделы" and sec_name != lib_section:
            continue
        for b in book_list:
            curr_st = st.session_state.book_statuses.get(b["title"], b["status"])
            if status_book_filter != "Все статусы" and curr_st != status_book_filter:
                continue
            if book_search.strip():
                q_b = book_search.strip().lower()
                if q_b not in b["title"].lower() and q_b not in b["author"].lower() and q_b not in b["desc"].lower():
                    continue
            b_copy = b.copy()
            b_copy["section"] = sec_name
            b_copy["live_status"] = curr_st
            books_to_show.append(b_copy)

    st.caption(f"Отображено книг: {len(books_to_show)} из {len(all_books_flat)}")

    status_options = ["Прочитано", "В процессе", "В планах"]
    b_cols = st.columns(2)
    for idx, book in enumerate(books_to_show):
        b_title = book["title"]
        curr_status = book["live_status"]
        status_color = "#3fb950" if curr_status == "Прочитано" else ("#58a6ff" if curr_status == "В процессе" else "#8b949e")

        with b_cols[idx % 2]:
            st.markdown(f"""
            <div class="linear-card" style="margin-bottom: 6px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-weight:700; font-size:0.98rem;">📖 {b_title}</div>
                        <div style="font-size:0.8rem; color:#8b949e; margin-top:2px;">Автор: <b>{book['author']}</b> • {book['section']}</div>
                    </div>
                    <span class="pill-badge" style="color:{status_color}; border-color:{status_color};">{curr_status}</span>
                </div>
                <div style="font-size:0.84rem; color:#c9d1d9; margin-top:10px; line-height:1.45;">
                    {book['desc']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            new_st = st.selectbox(
                f"Статус книги {b_title}",
                options=status_options,
                index=status_options.index(curr_status),
                key=f"bk_st_{b_title}",
                label_visibility="collapsed"
            )
            if new_st != curr_status:
                st.session_state.book_statuses[b_title] = new_st
                st.rerun()
    # Блок визуализации стрика со светофором
    st.markdown("##### 🚦 Статус стрика и светофор активности")
    
    # Получаем данные из нашего движка
    streak_data = CoreEngine.calculate_streak_traffic_light(df_rpg)
    current_streak = streak_data["streak"]
    status_map = streak_data["status_map"]

    # Выводим текущий стрик с пояснением про 3 дня буфера
    st.markdown(f"""
    <div class="linear-card" style="display: flex; align-items: center; justify-content: space-between;">
        <div>
            <div style="font-size: 0.78rem; color: #8b949e; text-transform: uppercase;">Текущая серия (Streak)</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #58a6ff;">🔥 {current_streak} дней подряд</div>
        </div>
        <div style="text-align: right; font-size: 0.8rem; color: #8b949e;">
            Буфер защиты: <b>3 дня пропуска</b><br>до сброса стрика
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Рисуем мини-светофор из последних дней
    st.markdown("<div style='font-size: 0.85rem; color: #8b949e; margin-bottom: 6px;'>История по дням (Светофор):</div>", unsafe_allow_html=True)
    
    # Генерируем HTML-блоки для отображения цвета каждого дня
    indicators_html = "<div style='display: flex; gap: 6px; flex-wrap: wrap;'>"
    if status_map:
        for d_date, color_type in list(status_map.items())[-14:]: # показываем последние 14 дней
            if color_type == "green":
                bg_col = "#3fb950"
                tooltip = f"{d_date}: Все выполнено (Зеленый)"
            elif color_type == "yellow":
                bg_col = "#d29922"
                tooltip = f"{d_date}: Частично выполнено (Желтый)"
            else:
                bg_col = "#f85149"
                tooltip = f"{d_date}: Пропуск (Красный)"
                
            indicators_html += f"""
            <div title="{tooltip}" style="width: 24px; height: 24px; background-color: {bg_col}; border-radius: 4px; display: inline-block; cursor: pointer;"></div>
            """
    else:
        indicators_html += "<span style='color: #8b949e; font-size: 0.85rem;'>Пока нет записей в RPG-логах. Заполни отчет за день!</span>"
    
    indicators_html += "</div>"
    st.markdown(indicators_html, unsafe_allow_html=True)
