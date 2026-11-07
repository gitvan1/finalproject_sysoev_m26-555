"""Хранилище Parser Service: rates.json (снимок) и exchange_rates.json (история)."""

from datetime import datetime, timezone

from ..infra.database import DatabaseManager
from .config import ParserConfig


class Storage:
    """Чтение/запись rates.json и exchange_rates.json."""

    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()
        self.db = DatabaseManager()

    def save_snapshot(
        self,
        prices: dict[str, float],
        sources: dict[str, str],
        timestamp: datetime | None = None,
    ) -> dict:
        """
        rates.json — снимок для Core Service.
        Совместим с usecases._get_rates).
        """

        now = timestamp or datetime.now(timezone.utc)
        now_iso = now.isoformat(timespec="seconds")

        # читаем текущий rates.json 
        current = self.db.load(self.config.RATES_FILE_PATH, default={})
        if not isinstance(current, dict):
            current = {}

        # оставляем старые пары, обновляем только переданные
        merged: dict = {
            k: v for k, v in current.items()
            if k not in ("source", "last_refresh")
        }

        for pair, rate in prices.items():
            merged[pair] = {
                "rate": float(rate),
                "updated_at": now_iso,
                "source": sources.get(pair, "ParserService"),
            }
        merged["source"] = "ParserService"
        merged["last_refresh"] = now_iso

        self.db.save(self.config.RATES_FILE_PATH, merged)
        return merged

    def append_history(
        self,
        prices: dict[str, float],
        sources: dict[str, str],
        timestamp: datetime | None = None,
    ) -> list[dict]:
        """exchange_rates.json — история измерений."""

        now = timestamp or datetime.now(timezone.utc)
        now_iso = now.isoformat(timespec="seconds")

        history = self.db.load(self.config.HISTORY_FILE_PATH, default=[])

        for pair, rate in prices.items():
            frm, to = pair.split("_", 1)
            record = {
                "id": f"{frm}_{to}_{now_iso}",
                "from_currency": frm,
                "to_currency": to,
                "rate": float(rate),
                "timestamp": now_iso,
                "source": sources.get(pair, "ParserService"),
            }

            if not any(r.get("id") == record["id"] for r in history):
                history.append(record)

        self.db.save(self.config.HISTORY_FILE_PATH, history)
        return history