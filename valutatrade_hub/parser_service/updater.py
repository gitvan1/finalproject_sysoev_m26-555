import logging
from datetime import datetime, timezone

from ..core.exceptions import ApiRequestError
from .api_clients import BaseApiClient
from .config import ParserConfig
from .storage import Storage

logger = logging.getLogger("valutatrade.parser")


class RatesUpdater:
    """
    Точка входа Parser Service.
    Опрашивает всех клиентов, объединяет результаты, передаёт в storage.
    """

    def __init__(
        self,
        clients: list[BaseApiClient],
        storage: Storage,
        config: ParserConfig | None = None,
    ):
        self.clients = clients
        self.storage = storage
        self.config = config or ParserConfig()

    def run_update(self) -> dict[str, dict]:
        """
        Один цикл обновления.

        Возвращает сохранённый снимок rates.json:
        """
        started = datetime.now(timezone.utc)
        logger.info(f"update started at {started.isoformat(timespec='seconds')}")

        merged: dict[str, float] = {}
        sources: dict[str, str] = {}
        errors: list[str] = []

        for client in self.clients:
            name = client.__class__.__name__
            logger.info(f"fetching from {name}")
            try:
                rates = client.fetch_rates()
            except ApiRequestError as exc:
                logger.error(f"{name} failed: {exc}")
                errors.append(f"{name}: {exc}")
                continue
            except Exception as exc:
                logger.exception(f"{name} crashed unexpectedly: {exc}")
                errors.append(f"{name}: {exc}")
                continue

            if not rates:
                logger.warning(f"{name} returned empty result")
                continue

            logger.info(f"{name} returned {len(rates)} pair(s)")
            for pair, rate in rates.items():
                merged[pair] = float(rate)
                sources[pair] = name

        if not merged:
            logger.error("no rates collected; update aborted")
            raise ApiRequestError(
                "Не удалось получить курсы ни от одного клиента"
                + (f" ({'; '.join(errors)})" if errors else "")
            )

        snapshot = self.storage.save_snapshot(
            prices=merged,
            sources=sources,
        )
        self.storage.append_history(
            prices=merged,
            sources=sources,
            timestamp=started,
        )

        finished = datetime.now(timezone.utc)
        logger.info(
            f"update finished in {(finished - started).total_seconds():.3f}s, "
            f"{len(merged)} pair(s) saved"
        )
        return snapshot