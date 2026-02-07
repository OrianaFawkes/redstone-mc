from datetime import datetime, timezone
from utils.state import load_state, save_state

DAILY_LIMIT = 2
WEEKLY_LIMIT = 5


def _now_utc():
    return datetime.now(timezone.utc)


def _today():
    return _now_utc().strftime("%Y-%m-%d")


def _week():
    return _now_utc().strftime("%Y-W%U")


class BackupState:
    def __init__(self):
        raw = load_state().get("backups", {})
        self.daily = raw.get("daily", {})
        self.weekly = raw.get("weekly", {})

    def can_backup(self) -> bool:
        return (
            self.daily.get(_today(), 0) < DAILY_LIMIT
            and self.weekly.get(_week(), 0) < WEEKLY_LIMIT
        )

    def record_backup(self):
        self.daily[_today()] = self.daily.get(_today(), 0) + 1
        self.weekly[_week()] = self.weekly.get(_week(), 0) + 1
        self.persist()

    def persist(self):
        state = load_state()
        state["backups"] = {"daily": self.daily, "weekly": self.weekly}
        save_state(state)
