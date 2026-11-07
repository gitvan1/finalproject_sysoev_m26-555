from abc import ABC, abstractmethod

import requests

from ..core.exceptions import ApiRequestError
from .config import ParserConfig


class BaseApiClient(ABC):
    """Базовый клиент."""
    
    def __init__(self, config: ParserConfig):
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> dict[str, float]:
        """
        Возвращает {PAIR: rate}, где PAIR = f"{FROM}_{TO}" в верхнем регистре.
        Бросает ApiRequestError при сбое сети или API.
        """

    @staticmethod
    def _get(url: str, timeout: int) -> dict:
        """GET-запрос с единой обработкой ошибок. Возвращает JSON."""
        try:
            response = requests.get(url, timeout=timeout)
        except requests.exceptions.RequestException as exc:
            raise ApiRequestError(f"Сетевая ошибка: {exc}") from exc

        if response.status_code != 200:
            raise ApiRequestError(
                f"HTTP {response.status_code} от {url}: {response.text[:200]}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise ApiRequestError(f"Некорректный JSON от {url}: {exc}") from exc
        
class CoinGeckoClient(BaseApiClient):
    """CoinGecko: криптовалюты к BASE_CURRENCY."""

    def fetch_rates(self) -> dict[str, float]:
        base = self.config.BASE_CURRENCY.lower()
        ids = ",".join(self.config.CRYPTO_ID_MAP.values())

        url = (
            f"{self.config.COINGECKO_URL}"
            f"?ids={ids}&vs_currencies={base}"
        )

        data = self._get(url, timeout=self.config.REQUEST_TIMEOUT)

        result = {}
        for code, cg_id in self.config.CRYPTO_ID_MAP.items():
            entry = data.get(cg_id)
            if not isinstance(entry, dict) or base not in entry:
                continue
            try:
                rate = float(entry[base])
            except (TypeError, ValueError):
                continue
            if rate <= 0:
                continue
            result[f"{code}_{self.config.BASE_CURRENCY}"] = rate

        if not result:
            raise ApiRequestError(
                "CoinGecko: в ответе нет ни одного ожидаемого курса"
            )
        return result
    
class ExchangeRateApiClient(BaseApiClient):
    """ExchangeRate-API: фиатные валюты к BASE_CURRENCY."""

    def fetch_rates(self) -> dict[str, float]:
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError(
                "ExchangeRate-API: не задан EXCHANGERATE_API_KEY"
            )

        url = (
            f"{self.config.EXCHANGERATE_API_URL}/"
            f"{self.config.EXCHANGERATE_API_KEY}/"
            f"latest/{self.config.BASE_CURRENCY}"
            )
        data = self._get(url, timeout=self.config.REQUEST_TIMEOUT)

        if data.get("result") != "success":
            reason = data.get("error-type") or data.get("error") or "unknown"
            raise ApiRequestError(f"ExchangeRate-API: {reason}")

        rates = data.get("conversion_rates")
        if not isinstance(rates, dict):
            raise ApiRequestError("ExchangeRate-API: нет поля 'conversion_rates'")

        result = {}
        base = self.config.BASE_CURRENCY

        for code in self.config.FIAT_CURRENCIES:
            rate = rates.get(code)
            try:
                rate = float(rate)
            except (TypeError, ValueError):
                continue
            if rate <= 0:
                continue

            result[f"{code}_{base}"] = 1.0 / rate

        if not result:
            raise ApiRequestError(
                "ExchangeRate-API: в ответе нет ни одного ожидаемого курса"
            )
        return result