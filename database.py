from datetime import date
import pandas as pd
from supabase import create_client, Client

class DatabaseManager:
    # Твои данные подключения к Supabase
    SUPABASE_URL = "https://jxqrmxfzzplspfkwhrij.supabase.co"
    SUPABASE_KEY = "Sb_secret_G05JIC-LWGWN7kalu4cDiA_AyUkJ-97"

    @classmethod
    def get_client(cls) -> Client:
        return create_client(cls.SUPABASE_URL, cls.SUPABASE_KEY)

    @classmethod
    def init_db(cls):
        """
        В Supabase таблицы создаются через веб-интерфейс (Table Editor).
        Здесь мы можем автоматически проверять/создавать дефолтного основателя (Igor_Founder).
        """
        supabase = cls.get_client()
        try:
            res = supabase.table("users").select("id").eq("username", "Igor_Founder").execute()
            if not res.data:
                supabase.table("users").insert({
                    "username": "Igor_Founder",
                    "pin_code": "0000",
                    "is_pro": 1,
                    "created_at": str(date.today())
                }).execute()
        except Exception as e:
            print(f"Ошибка при инициализации в Supabase: {e}")

    @classmethod
    def authenticate_or_register(cls, username: str, pin_code: str, create_new: bool = False):
        supabase = cls.get_client()
        username = username.strip()
        if not username or not pin_code:
            return None, "Введите никнейм и PIN-код!"

        if create_new:
            try:
                # Проверяем, есть ли уже такой
                existing = supabase.table("users").select("id").eq("username", username).execute()
                if existing.data:
                    return None, "Пользователь с таким ником уже существует!"
                
                # Создаем нового
                res = supabase.table("users").insert({
                    "username": username,
                    "pin_code": pin_code,
                    "is_pro": 0,
                    "created_at": str(date.today())
                }).execute()
            except Exception as e:
                return None, f"Ошибка регистрации: {e}"

        # Авторизация
        try:
            res = supabase.table("users").select("id, username, is_pro").eq("username", username).eq("pin_code", pin_code).execute()
            if res.data:
                row = res.data[0]
                return {"id": row["id"], "username": row["username"], "is_pro": bool(row["is_pro"])}, None
        except Exception as e:
            return None, f"Ошибка авторизации: {e}"

        return None, "Неверный никнейм или PIN-код!"

    @classmethod
    def set_pro_status(cls, user_id: int, is_pro: bool):
        supabase = cls.get_client()
        try:
            supabase.table("users").update({"is_pro": int(is_pro)}).eq("id", user_id).execute()
        except Exception as e:
            print(f"Ошибка обновления PRO статуса: {e}")

    @classmethod
    def save_health_log(cls, data: tuple):
        # Распаковываем кортеж аргументов в словарь для Supabase
        # (user_id, log_date, sleep_hours, sleep_quality, study_hours, eye_strain, training_type, training_intensity, head_impact, readiness_score, ai_advice)
        payload = {
            "user_id": data[0],
            "log_date": data[1],
            "sleep_hours": data[2],
            "sleep_quality": data[3],
            "study_hours": data[4],
            "eye_strain": data[5],
            "training_type": data[6],
            "training_intensity": data[7],
            "head_impact": data[8],
            "readiness_score": data[9],
            "ai_advice": data[10]
        }
        supabase = cls.get_client()
        try:
            # upsert заменяет запись, если совпадает UNIQUE (user_id, log_date)
            supabase.table("daily_health_logs").upsert(payload, on_conflict="user_id,log_date").execute()
        except Exception as e:
            print(f"Ошибка сохранения health log: {e}")

    @classmethod
    def save_rpg_log(cls, data: tuple):
        # (user_id, log_date, exercises_reps, agility_drills, book_pages, topics_learned, tasks_solved, plan_text, plan_percent, total_actions, xp_earned, str_pts, agi_pts, int_pts, dsc_pts, rpg_advice, daily_note)
        payload = {
            "user_id": data[0],
            "log_date": data[1],
            "exercises_reps": data[2],
            "agility_drills": data[3],
            "book_pages": data[4],
            "topics_learned": data[5],
            "tasks_solved": data[6],
            "plan_text": data[7],
            "plan_percent": data[8],
            "total_actions": data[9],
            "xp_earned": data[10],
            "str_pts": data[11],
            "agi_pts": data[12],
            "int_pts": data[13],
            "dsc_pts": data[14],
            "rpg_advice": data[15],
            "daily_note": data[16]
        }
        supabase = cls.get_client()
        try:
            supabase.table("rpg_actions_logs").upsert(payload, on_conflict="user_id,log_date").execute()
        except Exception as e:
            print(f"Ошибка сохранения rpg log: {e}")

    @classmethod
    def load_health_logs(cls, user_id: int) -> pd.DataFrame:
        supabase = cls.get_client()
        try:
            res = supabase.table("daily_health_logs").select("*").eq("user_id", user_id).order("log_date", desc=True).execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception as e:
            print(f"Ошибка загрузки health logs: {e}")
        return pd.DataFrame()

    @classmethod
    def load_rpg_logs(cls, user_id: int) -> pd.DataFrame:
        supabase = cls.get_client()
        try:
            res = supabase.table("rpg_actions_logs").select("*").eq("user_id", user_id).order("log_date", desc=True).execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception as e:
            print(f"Ошибка загрузки rpg logs: {e}")
        return pd.DataFrame()

    @classmethod
    def unlock_achievement(cls, user_id: int, ach_code: str):
        supabase = cls.get_client()
        try:
            # Вставляем игнорируя дубликаты (в Supabase через upsert с do_nothing или проверкой)
            existing = supabase.table("achievements").select("id").eq("user_id", user_id).eq("ach_code", ach_code).execute()
            if not existing.data:
                supabase.table("achievements").insert({
                    "user_id": user_id,
                    "ach_code": ach_code,
                    "unlocked_date": str(date.today())
                }).execute()
        except Exception as e:
            print(f"Ошибка разблокировки ачивки: {e}")

    @classmethod
    def get_unlocked_achievements(cls, user_id: int) -> dict:
        supabase = cls.get_client()
        try:
            res = supabase.table("achievements").select("ach_code, unlocked_date").eq("user_id", user_id).execute()
            if res.data:
                return {r["ach_code"]: r["unlocked_date"] for r in res.data}
        except Exception as e:
            print(f"Ошибка получения ачивок: {e}")
        return {}

    @classmethod
    def get_leaderboard(cls) -> pd.DataFrame:
        supabase = cls.get_client()
        try:
            # Вытягиваем всех пользователей, их RPG логи и ачивки для формирования рейтинга через Pandas
            users_res = supabase.table("users").select("id, username, is_pro").execute()
            rpg_res = supabase.table("rpg_actions_logs").select("user_id, xp_earned").execute()
            ach_res = supabase.table("achievements").select("user_id, ach_code").execute()

            users_df = pd.DataFrame(users_res.data) if users_res.data else pd.DataFrame(columns=["id", "username", "is_pro"])
            rpg_df = pd.DataFrame(rpg_res.data) if rpg_res.data else pd.DataFrame(columns=["user_id", "xp_earned"])
            ach_df = pd.DataFrame(ach_res.data) if ach_res.data else pd.DataFrame(columns=["user_id", "ach_code"])

            if users_df.empty:
                return pd.DataFrame(columns=["Игрок", "Статус", "Всего_XP", "Уровень", "Трофеев"])

            # Считаем сумму XP по пользователям
            xp_grouped = rpg_df.groupby("user_id")["xp_earned"].sum().reset_index() if not rpg_df.empty else users_df[["id"]].assign(xp_earned=0)
            
            # Считаем уникальные ачивки по пользователям
            ach_grouped = ach_df.groupby("user_id")["ach_code"].nunique().reset_index(name="Трофеев") if not ach_df.empty else users_df[["id"]].assign(Трофеев=0)

            # Объединяем всё в один датафрейм
            df = users_df.merge(xp_grouped, left_on="id", right_on="user_id", how="left").fillna(0)
            df = df.merge(ach_grouped, on="id", how="left").fillna(0)

            df["Статус"] = df["is_pro"].apply(lambda x: "💎 PRO" if int(x) == 1 else "🆓 FREE")
            df["Всего_XP"] = df["xp_earned"].astype(int)
            df["Уровень"] = (df["Всего_XP"] // 500) + 1
            df["Игрок"] = df["username"]
            df["Трофеев"] = df["Трофеев"].astype(int)

            df = df.sort_values(by="Всего_XP", ascending=False)
            return df[["Игрок", "Статус", "Всего_XP", "Уровень", "Трофеев"]]
        except Exception as e:
            print(f"Ошибка формирования лидерборда: {e}")
            return pd.DataFrame(columns=["Игрок", "Статус", "Всего_XP", "Уровень", "Трофеев"])

    @classmethod
    def get_goals(cls, user_id: int) -> pd.DataFrame:
        supabase = cls.get_client()
        try:
            res = supabase.table("user_goals").select("*").eq("user_id", user_id).execute()
            if res.data and len(res.data) > 0:
                return pd.DataFrame(res.data)
            
            # Если целей нет, создаем дефолтные
            defaults = [
                {"user_id": user_id, "goal_period": "month", "goal_title": "Закрыть план на 100% дней", "target_value": 30, "current_value": 5, "unit": "дн"},
                {"user_id": user_id, "goal_period": "month", "goal_title": "Решить задач по коду/ЕГЭ", "target_value": 100, "current_value": 22, "unit": "задач"},
                {"user_id": user_id, "goal_period": "year", "goal_title": "Сделать суммарно повторений ОФП", "target_value": 10000, "current_value": 1450, "unit": "повт"},
                {"user_id": user_id, "goal_period": "year", "goal_title": "Прочитать страниц литературы", "target_value": 1500, "current_value": 320, "unit": "стр"}
            ]
            supabase.table("user_goals").insert(defaults).execute()

            res_new = supabase.table("user_goals").select("*").eq("user_id", user_id).execute()
            return pd.DataFrame(res_new.data) if res_new.data else pd.DataFrame()
        except Exception as e:
            print(f"Ошибка работы с целями: {e}")
            return pd.DataFrame()

    @classmethod
    def update_goal_progress(cls, goal_id: int, new_val: float):
        supabase = cls.get_client()
        try:
            supabase.table("user_goals").update({"current_value": new_val}).eq("id", goal_id).execute()
        except Exception as e:
            print(f"Ошибка обновления прогресса цели: {e}")
