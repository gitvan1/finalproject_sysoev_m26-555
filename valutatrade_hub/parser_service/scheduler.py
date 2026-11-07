"""Периодический запуск Parser Service."""

import logging
import time

from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .config import ParserConfig
from .storage import Storage
from .updater import RatesUpdater

logger = logging.getLogger("valutatrade.parser.scheduler")


def run_forever(interval: int = 300, source: str | None = None) -> None:
    """Бесконечно обновляет курсы каждые 'interval' секунд."""
    config = ParserConfig()
    src = (source or "all").lower()

    clients = []
    if src in ("all", "coingecko"):
        clients.append(CoinGeckoClient(config))
    if src in ("all", "exchangerate"):
        clients.append(ExchangeRateApiClient(config))
    if not clients:
        raise ValueError(f"Неизвестный источник: {source}")

    updater = RatesUpdater(
        clients=clients,
        storage=Storage(config),
        config=config,
    )

    logger.info(f"scheduler started: interval={interval}s, source={src}")

    while True:
        try:
            updater.run_update()
        except Exception as exc:
            logger.exception(f"update failed: {exc}")

        logger.info(f"sleeping {interval}s")
        time.sleep(interval)