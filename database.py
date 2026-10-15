import sqlite3
from datetime import date
import pandas as pd


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

        # Дефолтный аккаунт основателя
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
        if not username or not pin_code:
            conn.close()
            return None, "Введите никнейм и PIN-код!"

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

        c.execute(
            "SELECT id, username, is_pro FROM users WHERE username = ? AND pin_code = ?",
            (username, pin_code)
        )
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

    @classmethod
    def get_leaderboard(cls) -> pd.DataFrame:
        conn = cls.get_conn()
        query = """
            SELECT 
                u.username AS Игрок,
                CASE WHEN u.is_pro = 1 THEN '💎 PRO' ELSE '🆓 FREE' END AS Статус,
                COALESCE(SUM(r.xp_earned), 0) AS Всего_XP,
                (COALESCE(SUM(r.xp_earned), 0) / 500) + 1 AS Уровень,
                COUNT(DISTINCT a.ach_code) AS Трофеев
            FROM users u
            LEFT JOIN rpg_actions_logs r ON u.id = r.user_id
            LEFT JOIN achievements a ON u.id = a.user_id
            GROUP BY u.id
            ORDER BY Всего_XP DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
