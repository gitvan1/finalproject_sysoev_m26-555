from abc import ABC, abstractmethod

from .exceptions import CurrencyNotFoundError, CurrencyValidationError


class Currency(ABC):
    """
    Абстрактная валюта.

    Атрибуты:
      name: str — человекочитаемое имя ("US Dollar", "Bitcoin").
      code: str — ISO-код или тикер ("USD", "EUR", "BTC"), upper, 2–5 символов.
    """

    def __init__(self, name: str, code: str):
        self.name = self._validate_name(name)
        self.code = self._validate_code(code)

    # Валидация 
    @staticmethod
    def _validate_name(name: str) -> str:
        if not isinstance(name, str) or not name.strip():
            raise CurrencyValidationError(
                "Имя валюты должно быть непустой строкой"
            )
        return name.strip()

    @staticmethod
    def _validate_code(code: str) -> str:
        if not isinstance(code, str):
            raise CurrencyValidationError("Код валюты должен быть строкой")
        code = code.strip().upper()
        if not (2 <= len(code) <= 5):
            raise CurrencyValidationError(
                f"Код валюты должен быть 2–5 символов, получено: '{code}'"
            )
        if any(ch.isspace() for ch in code):
            raise CurrencyValidationError(
                f"Код валюты не должен содержать пробелов: '{code}'"
            )
        return code
    
    # Абстрактное поведение
    @abstractmethod
    def get_display_info(self) -> str:
        """Строковое представление для UI/логов"""

class FiatCurrency(Currency):
    """Фиатная валюта: USD, EUR, RUB, ..."""

    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)

        if not isinstance(issuing_country, str) or not issuing_country.strip():
            raise CurrencyValidationError(
                "issuing_country должен быть непустой строкой"
            )
        self.issuing_country = issuing_country.strip()

    def get_display_info(self) -> str:
        return (
            f"[FIAT] {self.code} — {self.name} "
            f"(Issuing: {self.issuing_country})"
        )
    
class CryptoCurrency(Currency):
    """Криптовалюта: BTC, ETH …"""

    def __init__(
            self,
            name: str, 
            code: str, 
            algorithm: str,
            market_cap: float
        ):
        super().__init__(name, code)

        if not isinstance(algorithm, str) or not algorithm.strip():
            raise CurrencyValidationError(
                "algorithm должен быть непустой строкой"
            )
        self.algorithm = algorithm.strip()

        if isinstance(market_cap, bool) or not isinstance(market_cap, (int, float)):
            raise CurrencyValidationError(
                "market_cap должен быть числом"
            )
        if market_cap < 0:
            raise CurrencyValidationError(
                "market_cap не может быть отрицательным"
            )
        self.market_cap = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )
    
# Реестр валют 
_REGISTRY: dict[str, Currency] = {}

def register_currency(currency: Currency) -> None:
    """Добавляет валюту в реестр."""
    _REGISTRY[currency.code] = currency

def get_currency(code: str) -> Currency:
    """Возвращает валюту по коду."""
    if not isinstance(code, str) or not code.strip():
        raise CurrencyValidationError("Код валюты должен быть непустой строкой")

    key = code.strip().upper()
    currency = _REGISTRY.get(key)
    if currency is None:
        raise CurrencyNotFoundError(key)
    return currency

def _set_default_register() -> None:
    defaults: list[Currency] = [
        FiatCurrency("US Dollar", "USD", "United States"),
        FiatCurrency("Euro", "EUR", "Eurozone"),
        FiatCurrency("Russian Ruble", "RUB", "Russia"),
        CryptoCurrency("Bitcoin", "BTC", algorithm="SHA-256", market_cap=1.12e12),
        CryptoCurrency("Ethereum", "ETH", algorithm="Ethash", market_cap=4.5e11),
    ]
    for currency in defaults:
        register_currency(currency)

_set_default_register()
