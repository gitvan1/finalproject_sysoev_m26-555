# Базовое исключение
class ValutaTradeError(Exception):
    """Базовое исключение проекта."""

# Бизнес-ошибки
class RegisterError(ValutaTradeError):
    """Ошибка бизнес-логики регистрации."""

class LoginError(ValutaTradeError):
    """Ошибка бизнес-логики входа."""

class PortfolioError(ValutaTradeError):
    """Бизнес-ошибка портфеля"""

class RateError(ValutaTradeError):
    """Бизнес-ошибка получения курса."""

# Валюты 
class CurrencyError(ValutaTradeError):
    """Базовая ошибка работы с валютами."""

class CurrencyNotFoundError(CurrencyError):
    """Неизвестная валюта."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")

class CurrencyValidationError(ValutaTradeError, ValueError):
    """Некорректные данные валюты (код, имя, параметры)."""

# Средства
class InsufficientFundsError(ValutaTradeError):
    """Недостаточно средств на кошельке."""

    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        super().__init__(
            f"Недостаточно средств: доступно {available:.4f} {code}, "
            f"требуется {required:.4f} {code}"
        )

# Внешний API
class ApiRequestError(ValutaTradeError):
    """Сбой внешнего API."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")