import sqlite3
from datetime import date
import pandas as pd
import streamlit as st

# --- 1. НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(
    page_title="NeuroGuard & RPG Tracker",
    page_icon="⚡",
    layout="wide"
)

# --- 2. БАЗА ДАННЫХ SQLITE (ДВЕ ТАБЛИЦЫ: ЗДОРОВЬЕ + RPG) ---
def init_db():
    conn = sqlite3.connect("recovery_tracker.db")
    c = conn.cursor()
    # Таблица 1: Восстановление и здоровье
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
    # Таблица 2: RPG-прокачка и план дня
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
            rpg_advice TEXT
        )
    """)
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
            total_actions, xp_earned, str_pts, agi_pts, int_pts, dsc_pts, rpg_advice
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    # Очки характеристик за день
    str_pts = int(round(ex_reps * 0.4))
    agi_pts = int(round(agi_drills * 3.0 + ex_reps * 0.15))
    int_pts = int(round(pages * 0.8 + topics * 15 + tasks * 5))
    dsc_pts = int(round(plan_pct * 0.5))
    
    # Общее количество полезных действий за день
    total_actions = ex_reps + agi_drills + pages + topics + tasks
    
    # Опыт (XP) с бонусом за выполнение плана
    base_xp = (str_pts + agi_pts + int_pts) * 2
    multiplier = 1.0 + (plan_pct / 200.0)  # До +50% XP при 100% плане
    xp_earned = int(round(base_xp * multiplier))
    
    return str_pts, agi_pts, int_pts, dsc_pts, total_actions, xp_earned

init_db()
df_logs = load_logs()
df_rpg = load_rpg_logs()

# --- 4. САЙДБАР И ТЁМНАЯ ТЕМА ---
with st.sidebar:
    st.header("🎨 Интерфейс")
    dark_mode = st.toggle("🌙 Тёмная тема (Eye-Safe)", value=True)
    st.divider()
    st.markdown(
        "**Профиль игрока:**\n"
        "* 📚 Учеба: 10 класс (ЕГЭ / Код)\n"
        "* 🥋 Спорт: Единоборства и ОФП\n"
        "* 👀 Приоритет: Защита сетчатки и ЦНС"
    )

if dark_mode:
    st.markdown("""
        <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #0d1117 !important;
            color: #c9d1d9 !important;
        }
        [data-testid="stSidebar"] {
            background-color: #161b22 !important;
            border-right: 1px solid #30363d !important;
        }
        h1, h2, h3, h4, p, span, label, .stMarkdown, [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
            color: #e6edf3 !important;
        }
        div[data-baseweb="select"] > div, input, textarea {
            background-color: #21262d !important;
            color: #e6edf3 !important;
            border: 1px solid #30363d !important;
        }
        .status-box {
            padding: 12px 16px;
            border-radius: 8px;
            font-weight: 600;
            margin-bottom: 15px;
            border: 1px solid #30363d;
        }
        .rpg-card {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .status-box {
            padding: 12px 16px;
            border-radius: 8px;
            font-weight: 600;
            margin-bottom: 15px;
        }
        .rpg-card {
            background-color: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 5. ПЕРЕКЛЮЧАТЕЛЬ ДВУХ МЕСТ (ВКЛАДКИ ВЕРХНЕГО УРОВНЯ) ---
st.title("⚡ NeuroGuard: Здоровье & RPG-Прокачка")

main_tab1, main_tab2 = st.tabs([
    "🛡️ 1. Мониторинг здоровья",
    "⚔️ 2. RPG-Прокачка и План дня"
])

# =====================================================================
# МЕСТО 1: МОНИТОРИНГ ЗДОРОВЬЯ И ВОССТАНОВЛЕНИЯ
# =====================================================================
with main_tab1:
    st.write("Контроль когнитивного ресурса, зрительного утомления и физической готовности.")
    col_input, col_result = st.columns([1.1, 1])

    with col_input:
        st.subheader("📊 Показатели за день")
        log_date = st.date_input("Дата записи", value=date.today(), key="health_date")
        
        c1, c2 = st.columns(2)
        with c1:
            sleep_hours = st.slider("Часы сна", 0.0, 12.0, 7.5, 0.5)
            study_hours = st.slider("Учеба и экраны (часы)", 0.0, 14.0, 5.0, 0.5)
            training_type = st.selectbox(
                "Тип физической нагрузки",
                ["Отдых", "ОФП / Турники / Бег", "Техника в воздух / Лапы (без контакта)", "Спарринги / Полный контакт"]
            )
        with c2:
            sleep_quality = st.slider("Качество сна (1–10)", 1, 10, 8)
            eye_strain = st.slider("Усталость / боль в глазах (1–10)", 1, 10, 3)
            
            is_rest = (training_type == "Отдых")
            training_intensity = st.slider(
                "Тяжесть тренировки (0–10)",
                0, 10,
                value=0 if is_rest else 5,
                disabled=is_rest
            )

        head_impact = st.checkbox("Были пропущенные удары в голову или резкое натуживание")
        analyze_btn = st.button("🚀 Рассчитать индекс и сохранить день", use_container_width=True, type="primary")

    with col_result:
        st.subheader("🧠 Вердикт системы")
        current_score = calculate_readiness(
            sleep_hours, sleep_quality, study_hours, eye_strain, training_intensity, head_impact
        )
        
        score_delta = None
        if not df_logs.empty:
            last_score = int(df_logs.iloc[0]["readiness_score"])
            score_delta = f"{current_score - last_score}% к прошлой записи"

        st.metric(
            label="Индекс готовности организма (Readiness Score)",
            value=f"{current_score}%",
            delta=score_delta
        )
        st.progress(current_score / 100)

        if current_score >= 70 and eye_strain <= 5 and not head_impact:
            st.markdown('<div class="status-box" style="background-color: rgba(46, 160, 67, 0.2); color: #3fb950;">🟢 Оптимальная готовность: ресурс в норме</div>', unsafe_allow_html=True)
        elif current_score >= 45 and eye_strain <= 7 and not head_impact:
            st.markdown('<div class="status-box" style="background-color: rgba(210, 153, 34, 0.2); color: #d29922;">🟡 Умеренное утомление: дозируй экран и спорт</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box" style="background-color: rgba(248, 81, 73, 0.2); color: #f85149;">🔴 Перегрузка / Риск для глаз: нужен режим восстановления!</div>', unsafe_allow_html=True)

        if analyze_btn:
            advice_parts = []
            if eye_strain >= 6 or head_impact:
                advice_parts.append("⚠️ **Зрение:** Высокий риск перегрузки сетчатки и аккомодации. Полностью исключи спарринги, резкие натуживания и сократи экранное время.")
            else:
                advice_parts.append("👀 **Зрение:** Нагрузка в пределах нормы, но при работе с кодом соблюдай правило 20-20-20 (каждые 20 минут смотри вдаль).")
            
            if current_score < 50:
                advice_parts.append("🔋 **Режим:** ЦНС перегружена. Завтра только легкая разминка и сон минимум 8 часов.")
            else:
                advice_parts.append("💪 **Режим:** Хороший тонус. Можно продуктивно ботать и делать ОФП / технику в воздух без контакта в голову.")
            
            advice = "\n\n".join(advice_parts)

            save_log((
                str(log_date), sleep_hours, sleep_quality, study_hours,
                eye_strain, training_type, training_intensity,
                int(head_impact), current_score, advice
            ))
            df_logs = load_logs()
            st.success("Запись за день сохранена!")
            st.markdown("### 📋 Рекомендация")
            st.info(advice)

    st.divider()
    st.subheader("📈 Динамика состояния и аналитика")
    if not df_logs.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Средний сон", f"{df_logs['sleep_hours'].mean():.1f} ч")
        m2.metric("Средняя усталость глаз", f"{df_logs['eye_strain'].mean():.1f} / 10")
        m3.metric("Средний индекс готовности", f"{df_logs['readiness_score'].mean():.0f}%")

        t1, t2 = st.tabs(["Графики нагрузки", "База записей"])
        with t1:
            chart_df = df_logs[["log_date", "readiness_score", "eye_strain", "sleep_hours"]].sort_values("log_date")
            st.line_chart(chart_df.set_index("log_date"))
        with t2:
            st.dataframe(df_logs, use_container_width=True)
    else:
        st.write("В базе пока нет записей. Нажми кнопку расчета выше, чтобы добавить первый день.")


# =====================================================================
# МЕСТО 2: RPG-ПРОКАЧКА ХАРАКТЕРИСТИК И ПЛАН НА ДЕНЬ
# =====================================================================
with main_tab2:
    st.write("Записывай результаты за день, закрывай пункты плана и прокачивай характеристики персонажа.")

    rpg_col1, rpg_col2 = st.columns([1.1, 1])

    with rpg_col1:
        st.subheader("📝 План на день и результаты")
        rpg_date = st.date_input("Дата прокачки", value=date.today(), key="rpg_date")

        # --- ПЛАН НА ДЕНЬ ---
        st.markdown("##### 🎯 Твой план на день")
        default_plan = "Сделать 100 подтягиваний\nРешить 5 задач по профилю/инфе\nПрочитать 15 страниц книги\nОтработать 3 раунда техники (бой с тенью)"
        plan_text = st.text_area(
            "Напиши задачи на день (каждая с новой строки):",
            value=default_plan,
            height=110
        )

        tasks_list = [t.strip() for t in plan_text.split("\n") if t.strip()]
        if tasks_list:
            st.caption("Отмечай выполненные пункты:")
            completed_tasks = 0
            for idx, task_item in enumerate(tasks_list):
                if st.checkbox(task_item, key=f"task_chk_{idx}"):
                    completed_tasks += 1
            plan_percent = int(round((completed_tasks / len(tasks_list)) * 100))
        else:
            plan_percent = st.slider("Процент выполнения плана (%)", 0, 100, 70)

        st.divider()

        # --- ВВОД КОЛИЧЕСТВА СДЕЛАННОГО ЗА ДЕНЬ ---
        st.markdown("##### 🏆 Сделано за день (в числах)")
        rc1, rc2 = st.columns(2)
        with rc1:
            exercises_reps = st.number_input("💪 Кол-во упражнений (подтягивания, отжимания и т.д.)", min_value=0, max_value=2000, value=100, step=10)
            agility_drills = st.number_input("⚡ Раунды техники / разминки / кобудо", min_value=0, max_value=50, value=3, step=1)
            book_pages = st.number_input("📖 Прочитано страниц книги", min_value=0, max_value=500, value=15, step=5)
        with rc2:
            topics_learned = st.number_input("🧠 Пройдено тем (учеба / инглиш / код)", min_value=0, max_value=20, value=1, step=1)
            tasks_solved = st.number_input("💻 Решено задач (ЕГЭ / Python / олимпиады)", min_value=0, max_value=200, value=5, step=1)

        save_rpg_btn = st.button("⚔️ Зафиксировать прокачку за день", use_container_width=True, type="primary")

    with rpg_col2:
        st.subheader("🎮 Статус Персонажа")

        # Расчет очков за текущий день
        str_pts, agi_pts, int_pts, dsc_pts, total_actions, xp_earned = calculate_rpg_stats(
            exercises_reps, agility_drills, book_pages, topics_learned, tasks_solved, plan_percent
        )

        # Суммарная статистика за всё время из базы + предпросмотр сегодняшнего дня
        hist_xp = int(df_rpg["xp_earned"].sum()) if not df_rpg.empty else 0
        hist_str = int(df_rpg["str_pts"].sum()) if not df_rpg.empty else 0
        hist_agi = int(df_rpg["agi_pts"].sum()) if not df_rpg.empty else 0
        hist_int = int(df_rpg["int_pts"].sum()) if not df_rpg.empty else 0
        hist_dsc = int(df_rpg["dsc_pts"].sum()) if not df_rpg.empty else 0

        total_xp = hist_xp + xp_earned
        player_level = (total_xp // 500) + 1
        xp_in_current_lvl = total_xp % 500

        # Карточка Уровня и XP
        st.markdown(f"""
        <div class="rpg-card">
            <h3 style="margin:0;">🏅 Уровень {player_level} <span style="font-size:16px; font-weight:normal;">({total_xp} XP всего | +{xp_earned} XP сегодня)</span></h3>
        </div>
        """, unsafe_allow_html=True)
        st.progress(xp_in_current_lvl / 500.0, text=f"До уровня {player_level + 1}: {xp_in_current_lvl} / 500 XP")

        # Показатели выполнения плана и общего количества действий
        k1, k2 = st.columns(2)
        k1.metric("🎯 Выполнение плана", f"{plan_percent}%", delta="Бонус к XP активен" if plan_percent >= 80 else None)
        k2.metric("🔥 Всего действий за день", f"{total_actions}", delta=f"+{xp_earned} XP")

        st.markdown("##### 📊 Прокачка характеристик:")
        s1, s2 = st.columns(2)
        with s1:
            st.markdown(f"**💪 Сила (STR):** `{hist_str + str_pts}` *(+{str_pts})*")
            st.progress(min(1.0, (hist_str + str_pts) / 500.0))
            st.markdown(f"**⚡ Ловкость (AGI):** `{hist_agi + agi_pts}` *(+{agi_pts})*")
            st.progress(min(1.0, (hist_agi + agi_pts) / 500.0))
        with s2:
            st.markdown(f"**🧠 Интеллект (INT):** `{hist_int + int_pts}` *(+{int_pts})*")
            st.progress(min(1.0, (hist_int + int_pts) / 500.0))
            st.markdown(f"**🛡️ Дисциплина (DSC):** `{hist_dsc + dsc_pts}` *(+{dsc_pts})*")
            st.progress(min(1.0, (hist_dsc + dsc_pts) / 500.0))

        # --- ГЕНЕРАЦИЯ СОВЕТА ПО ПОВЫШЕНИЮ ПРОЦЕНТА И ПРОКАЧКЕ ---
        rpg_tips = []
        if plan_percent < 50:
            rpg_tips.append("📉 **Как поднять % плана:** Ты взял слишком много крупных задач разом. Завтра разбей каждую задачу на 2 мелких шага (например, не «ботать матан», а «решить 3 задачи первой части») и закрывай самую сложную до обеда.")
        elif plan_percent < 85:
            rpg_tips.append("📈 **Как дожать план до 100%:** Отличный темп! Чтобы закрывать оставшиеся 15–30%, используй таймер Помодоро (25 минут фокуса без телефона + 5 минут отдыха для глаз).")
        else:
            rpg_tips.append("🔥 **Дисциплина на максимуме:** План выполнен на элитном уровне! Ты получаешь максимальный множитель опыта. Завтра можно повысить планку на +10% к ключевому навыку.")

        if str_pts + agi_pts > int_pts * 2:
            rpg_tips.append("⚖️ **Баланс статов:** Физуха и ловкость сегодня сильно обогнали Интеллект. Добавь завтра +3 задачи по коду/математике или 10 страниц книги, чтобы качать персонажа гармонично.")
        elif int_pts > (str_pts + agi_pts) * 2:
            rpg_tips.append("🤸 **Баланс статов:** Мощный упор в Интеллект! Чтобы разгрузить глаза и ЦНС после ботки, добавь завтра пару подходов на турнике или бой с тенью.")

        rpg_advice_text = "\n\n".join(rpg_tips)
        st.markdown("##### 💡 Совет системы: как увеличить результат")
        st.info(rpg_advice_text)

        if save_rpg_btn:
            save_rpg_log((
                str(rpg_date), exercises_reps, agility_drills, book_pages,
                topics_learned, tasks_solved, plan_text, plan_percent,
                total_actions, xp_earned, str_pts, agi_pts, int_pts, dsc_pts, rpg_advice_text
            ))
            df_rpg = load_rpg_logs()
            st.success("Прокачка за день сохранена в базу! Характеристики обновлены.")

    # --- ИСТОРИЯ ПРОКАЧКИ ---
    st.divider()
    st.subheader("📜 История прокачки и выполнения планов")
    if not df_rpg.empty:
        rt1, rt2 = st.tabs(["График продуктивности", "Таблица RPG-базы"])
        with rt1:
            rpg_chart = df_rpg[["log_date", "plan_percent", "total_actions", "xp_earned"]].sort_values("log_date")
            st.line_chart(rpg_chart.set_index("log_date"))
            st.caption("Динамика по дням: % выполнения плана, Общее кол-во действий и Заработанный опыт (XP).")
        with rt2:
            st.dataframe(df_rpg, use_container_width=True)
    else:
        st.write("В RPG-базе пока нет сохраненных дней. Отметь галочки плана и нажми **«Зафиксировать прокачку за день»**!")
