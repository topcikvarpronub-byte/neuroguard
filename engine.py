from datetime import datetime
import pandas as pd
from database import DatabaseManager
from achievements_data import ACHIEVEMENTS_CATALOG


class CoreEngine:
    @staticmethod
    def calculate_readiness(sleep_h: float, sleep_q: int, study_h: float,
                            eye_strain: int, train_int: int, head_impact: bool) -> int:
        sleep_recovery = min(sleep_h / 8.0, 1.15) * 60 + (sleep_q / 10.0) * 40
        cognitive_penalty = study_h * 2.0
        eye_penalty = max(0, (eye_strain - 1) * 3.8)
        physical_penalty = train_int * 2.2
        impact_penalty = 25 if head_impact else 0
        score = sleep_recovery - (cognitive_penalty + eye_penalty + physical_penalty + impact_penalty)
        return max(0, min(100, int(round(score))))

    @staticmethod
    def calculate_rpg_stats(ex_reps: int, agi_drills: int, pages: int,
                            topics: int, tasks: int, plan_pct: int, is_pro: bool = False):
        str_pts = int(round(ex_reps * 0.4))
        agi_pts = int(round(agi_drills * 3.0 + ex_reps * 0.15))
        int_pts = int(round(pages * 0.8 + topics * 15 + tasks * 5))
        dsc_pts = int(round(plan_pct * 0.5))

        total_actions = ex_reps + agi_drills + pages + topics + tasks
        base_xp = (str_pts + agi_pts + int_pts) * 2
        plan_multiplier = 1.0 + (plan_pct / 200.0)
        pro_multiplier = 1.25 if is_pro else 1.0
        xp_earned = int(round(base_xp * plan_multiplier * pro_multiplier))
        return str_pts, agi_pts, int_pts, dsc_pts, total_actions, xp_earned

    @staticmethod
    def get_rank_badge(score_or_pct: int):
        if score_or_pct >= 90:
            return "👑 S-РАНГ", "#f1e05a"
        elif score_or_pct >= 75:
            return "💎 A-РАНГ", "#3fb950"
        elif score_or_pct >= 50:
            return "⚔️ B-РАНГ", "#58a6ff"
        return "🛡️ C-РАНГ", "#d29922"

    @staticmethod
    def analyze_burnout_risk(df_health: pd.DataFrame, df_rpg: pd.DataFrame) -> dict:
        """Анализатор риска выгорания и перегрузки ЦНС"""
        if df_health is None or df_health.empty or len(df_health) < 1:
            return {
                "risk_level": "🟢 БАЗОВЫЙ УРОВЕНЬ",
                "color": "#3fb950",
                "message": "Сохрани первый био-статус во вкладке БИО, чтобы запустить предиктивный анализ выгорания."
            }

        recent_sleep = df_health["sleep_hours"].head(3).mean()
        recent_study = df_health["study_hours"].head(3).mean()
        recent_strain = df_health["eye_strain"].head(3).mean()

        risk_score = 0
        if recent_sleep < 6.5:
            risk_score += 45
        elif recent_sleep < 7.5:
            risk_score += 20

        if recent_study > 8.0:
            risk_score += 35
        elif recent_study > 6.0:
            risk_score += 15

        if recent_strain > 6.0:
            risk_score += 25

        if risk_score >= 65:
            return {
                "risk_level": "🔴 ВЫСОКИЙ РИСК ВЫГОРАНИЯ",
                "color": "#f85149",
                "message": f"⚠️ Внимание! Средний сон упал до {recent_sleep:.1f}ч при экранном времени {recent_study:.1f}ч. Риск истощения высок. Срочно добавь сон и выполни протокол резета во вкладке 🧘 РЕЗЕТ!"
            }
        elif risk_score >= 35:
            return {
                "risk_level": "🟡 УМЕРЕННАЯ НАГРУЗКА",
                "color": "#d29922",
                "message": f"⚡ Организм под нагрузкой. Следи за качеством сна ({recent_sleep:.1f}ч) и делай перерывы для глаз по правилу 20-20-20."
            }
        else:
            return {
                "risk_level": "🟢 БАЛАНС И ТОНУС",
                "color": "#3fb950",
                "message": "✅ Отличный баланс работы и восстановления. Риск выгорания минимален, все показатели в норме."
            }

    @staticmethod
    def evaluate_and_sync_achievements(user_id: int, df_health: pd.DataFrame, df_rpg: pd.DataFrame,
                                       curr_eye: int, curr_impact: bool, curr_study: float,
                                       curr_sleep: float, curr_sleep_q: int, curr_readiness: int,
                                       curr_plan: int, curr_reps: int, curr_drills: int,
                                       curr_tasks: int, curr_pages: int, curr_topics: int,
                                       curr_note: str):
        total_health_days = len(df_health) if df_health is not None else 0
        safe_head_days = int((df_health["head_impact"] == 0).sum()) if (df_health is not None and not df_health.empty) else 0

        sum_reps = (int(df_rpg["exercises_reps"].sum()) if (df_rpg is not None and not df_rpg.empty) else 0) + curr_reps
        sum_drills = (int(df_rpg["agility_drills"].sum()) if (df_rpg is not None and not df_rpg.empty) else 0) + curr_drills
        sum_tasks = (int(df_rpg["tasks_solved"].sum()) if (df_rpg is not None and not df_rpg.empty) else 0) + curr_tasks
        sum_pages = (int(df_rpg["book_pages"].sum()) if (df_rpg is not None and not df_rpg.empty) else 0) + curr_pages
        sum_topics = (int(df_rpg["topics_learned"].sum()) if (df_rpg is not None and not df_rpg.empty) else 0) + curr_topics
        sum_xp = (int(df_rpg["xp_earned"].sum()) if (df_rpg is not None and not df_rpg.empty) else 0)
        lvl = (sum_xp // 500) + 1

        perfect_plans = int((df_rpg["plan_percent"] == 100).sum()) if (df_rpg is not None and not df_rpg.empty) else 0
        if curr_plan == 100:
            perfect_plans += 1

        notes_count = int((df_rpg["daily_note"].fillna("") != "").sum()) if (df_rpg is not None and not df_rpg.empty) else 0
        if curr_note.strip():
            notes_count += 1

        triggers = {
            "BIO_01": (curr_eye <= 4 and not curr_impact),
            "BIO_02": (curr_eye <= 2),
            "BIO_03": (curr_study <= 3.0),
            "BIO_04": (curr_sleep >= 8.0 and curr_sleep_q >= 8),
            "BIO_05": (curr_readiness >= 85),
            "BIO_06": (curr_readiness >= 95),
            "BIO_07": (safe_head_days >= 3),
            "BIO_08": (safe_head_days >= 7),
            "BIO_09": (total_health_days >= 14),
            "SPT_01": (curr_reps >= 100),
            "SPT_02": (curr_reps >= 200),
            "SPT_03": (sum_reps >= 500),
            "SPT_04": (sum_reps >= 1000),
            "SPT_05": (curr_drills >= 3),
            "SPT_06": (curr_drills >= 5),
            "SPT_07": (curr_drills >= 10),
            "SPT_08": (sum_drills >= 25),
            "SPT_09": (sum_drills >= 50),
            "INT_01": (curr_tasks >= 5),
            "INT_02": (curr_tasks >= 10),
            "INT_03": (curr_tasks >= 20),
            "INT_04": (sum_tasks >= 50),
            "INT_05": (sum_tasks >= 100),
            "INT_06": (curr_pages >= 20),
            "INT_07": (curr_pages >= 50),
            "INT_08": (sum_pages >= 300),
            "INT_09": (sum_topics >= 15),
            "DSC_01": (curr_plan >= 80),
            "DSC_02": (curr_plan == 100),
            "DSC_03": (perfect_plans >= 3),
            "DSC_04": (notes_count >= 1),
            "DSC_05": (notes_count >= 7),
            "DSC_06": (lvl >= 2),
            "DSC_07": (lvl >= 5),
            "DSC_08": (lvl >= 10),
            "DSC_09": (lvl >= 20),
        }

        for code, is_met in triggers.items():
            if is_met:
                DatabaseManager.unlock_achievement(user_id, code)

        unlocked_map = DatabaseManager.get_unlocked_achievements(user_id)

        result_list = []
        for item in ACHIEVEMENTS_CATALOG:
            entry = item.copy()
            code = entry["code"]
            entry["unlocked"] = code in unlocked_map
            entry["date"] = unlocked_map.get(code, "")
            result_list.append(entry)

        return result_list

    @staticmethod
    def generate_weekly_report(username: str, is_pro: bool, df_health: pd.DataFrame, df_rpg: pd.DataFrame) -> str:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        tier = "PRO-Аккаунт 💎" if is_pro else "Базовый (Free)"
        lines = [
            "==========================================",
            "⚡ NEUROGUARD: ОФИЦИАЛЬНАЯ СВОДКА МОНИТОРИНГА",
            f"👤 Пользователь: {username} ({tier})",
            f"📅 Дата формирования: {now_str}",
            "==========================================\n",
            "1. МЕДИЦИНСКИЙ И БИО-ПРОФИЛЬ (ЗРЕНИЕ И ЦНС):"
        ]
        if df_health is not None and not df_health.empty:
            h7 = df_health.head(7)
            lines.append(f"• Записей проанализировано: {len(h7)} дн.")
            lines.append(f"• Средняя продолжительность сна: {h7['sleep_hours'].mean():.1f} ч")
            lines.append(f"• Средний индекс готовности ЦНС: {h7['readiness_score'].mean():.0f}%")
        else:
            lines.append("• Нет записей за период.")
        return "\n".join(lines)
