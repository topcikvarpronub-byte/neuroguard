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
    .saas-section-card {{
        background: rgba(19, 28, 46, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(88, 166, 255, 0.2);
        border-radius: 20px;
        padding: 30px;
        margin: 35px 0;
        box-shadow: 0 12px 40px rgba(0,0,0,0.4);
        text-align: left;
    }}
    .landing-container {{
        max-width: 900px;
        margin: 0 auto;
        text-align: center;
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
# ЭКРАН 1: 🌟 ЛЕНДИНГ С КАРТИНКАМИ И КАРТОЧКАМИ
# =====================================================================
if st.session_state.page == "landing":
    st.markdown("""
        <div class="landing-container">
            <span class="hud-pill pro-pill" style="margin-bottom: 15px;">🚀 v2.5 Enterprise Edition</span>
            <h1 style="font-size: 44px; font-weight: 800; margin-bottom: 15px; background: linear-gradient(90deg, #58a6ff, #3fb950); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">NEUROGUARD SaaS</h1>
            <p style="font-size: 18px; color: #c9d1d9; margin-bottom: 25px;">Гиперинтеллектуальная экосистема для глубокой продуктивности, биохакинга ЦНС и геймификации твоего потенциала.</p>
        </div>
    """, unsafe_allow_html=True)

    try:
        st.image("hero.jpg", use_container_width=True)
    except:
        pass

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2, c_btn3 = st.columns([1, 1.2, 1])
    with c_btn2:
        if st.button("⚡ Войти в систему / Начать", use_container_width=True, type="primary"):
            st.session_state.page = "auth"
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown("""
        <div class="saas-section-card">
            <h2 style="color: #58a6ff; margin-bottom: 10px;">🛡️ 1. Био-Мониторинг и Защита ЦНС</h2>
            <p style="color: #e6edf3; font-size: 15px; line-height: 1.6; margin: 0;">Интеллектуальный анализ сна, экранного времени и спазма глаз. Предиктивный алгоритм вычисляет уровень усталости и защищает от эмоционального выгорания в реальном времени.</p>
        </div>
    """, unsafe_allow_html=True)
    try:
        st.image("bio.jpg", use_container_width=True)
    except:
        pass

    st.markdown("""
        <div class="saas-section-card">
            <h2 style="color: #58a6ff; margin-bottom: 10px;">⚔️ 2. RPG-Прокачка и GitHub Heatmap</h2>
            <p style="color: #e6edf3; font-size: 15px; line-height: 1.6; margin: 0;">Преврати рутину в увлекательную игру. Накапливай опыт (XP), повышай уровень персонажа, выполняй ежедневные квесты и отслеживай продуктивность по яркой тепловой карте.</p>
        </div>
    """, unsafe_allow_html=True)
    try:
        st.image("rpg.jpg", use_container_width=True)
    except:
        pass

    st.markdown("""
        <div class="saas-section-card">
            <h2 style="color: #58a6ff; margin-bottom: 10px;">🏆 3. Зал Славы и 36 Трофеев</h2>
            <p style="color: #e6edf3; font-size: 15px; line-height: 1.6; margin: 0;">Коллекционируй уникальные достижения за выдающиеся успехи в учебе, олимпиадах, спорте (каратэ, кобудо, ОФП) и железную дисциплину.</p>
        </div>
    """, unsafe_allow_html=True)
    try:
        st.image("trophies.jpg", use_container_width=True)
    except:
        pass

    st.markdown("""
        <div class="saas-section-card">
            <h2 style="color: #58a6ff; margin-bottom: 10px;">🧘 4. Нейро-Резет и Умный Советник</h2>
            <p style="color: #e6edf3; font-size: 15px; line-height: 1.6; margin: 0;">Интерактивные таймеры пальминга, правила 20-20-20, дыхательные протоколы и персональный советник по восстановлению (растяжка, сауна, холодный душ).</p>
        </div>
    """, unsafe_allow_html=True)
    try:
        st.image("reset.jpg", use_container_width=True)
    except:
        pass

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn4, c_btn5, c_btn6 = st.columns([1, 1.2, 1])
    with c_btn5:
        if st.button("🚀 Начать использовать SaaS", use_container_width=True, type="primary"):
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
        st.markdown(f"Профиль: **`{cur_u['username']}`**
