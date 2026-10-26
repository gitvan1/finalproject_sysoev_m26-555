import hashlib
from datetime import datetime


class User:
    """Класс пользователя системы"""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str = "",
        salt: str = "",
        registration_date: datetime | None = None,
    ):
        # Приватные атрибуты
        self._user_id = user_id
        self._username = username
        self._salt = salt
        self._hashed_password = hashed_password
        self._registration_date = registration_date or datetime.now()

    # ГЕТТЕРЫ / СЕТТЕРЫ
    @property
    def user_id(self) -> int:
        return self._user_id

    @user_id.setter
    def user_id(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("user_id должен быть положительным целым числом")
        self._user_id = value

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        return self._hashed_password
    
    # У hashed_password нет сеттера, так как
    # менять пароль можно только через change_password()

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date
    
    # Публичные методы
    def get_user_info(self) -> dict:
        """Выводит и возвращает информацию о пользователе (без пароля)."""
        info = {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }
        print(
            f"User #{info['user_id']} | username: {info['username']!r} "
            f"| зарегистрирован: {info['registration_date']}"
        )
        return info
    
    def change_password(self, new_password: str) -> None:
        """Изменяет пароль пользователя (проверка длины + SHA-256 с солью)."""
        if not isinstance(new_password, str) or len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = hashlib.sha256(
            (new_password + self._salt).encode("utf-8")
        ).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Проверяет, соответствует ли введённый пароль сохранённому."""
        if not isinstance(password, str):
            return False
        candidate = hashlib.sha256(
            (password + self._salt).encode("utf-8")
        ).hexdigest()
        return candidate == self._hashed_password
    
class Wallet:
    """Кошелёк пользователя для одной конкретной валюты"""

    def __init__(
        self,
        currency_code: str,
        balance: float = 0.0
    ):
        self._currency_code = ""
        self.currency_code = currency_code 
        self._balance = 0.0
        self.balance = balance  

    # ГЕТТЕРЫ / СЕТТЕРЫ

    @property
    def currency_code(self) -> str:
        return self._currency_code

    @currency_code.setter
    def currency_code(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Код валюты не может быть пустым")
        self._currency_code = value.strip().upper()

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    # Публичные методы
    def deposit(self, amount: float) -> None:
        """Пополняет баланс."""
        self._validate_amount(amount)
        self._balance += float(amount)

    def withdraw(self, amount: float) -> None:
        """Снятие средств."""
        self._validate_amount(amount)
        if float(amount) > self._balance:
            raise ValueError(
                f"Недостаточно средств: баланс {self._balance} {self._currency_code}, "
                f"запрошено {amount}"
            )
        self._balance -= float(amount)

    def get_balance_info(self) -> dict:
        """Выводит и возвращает информацию о текущем балансе."""
        info = {
            "currency_code": self._currency_code,
            "balance": round(self._balance, 8),
        }
        print(f"{info['currency_code']}: {info['balance']}")
        return info

    # Служебные методы
    @staticmethod
    def _validate_amount(amount: float) -> None:
        """Проверка, что сумма операции - положительное число."""
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")
        
class Portfolio:
    """Управление всеми кошельками одного пользователя"""

    # Фиксированные курсы
    _DEFAULT_RATES: dict[str, float] = {
        "USD": 1.0,
        "EUR": 1.08,
        "BTC": 65000.0,
        "ETH": 3200.0,
    }

    def __init__(
        self, 
        user_id: int,
        wallets: dict[str, "Wallet"] | None = None,
        user: "User" | None = None
    ):
        
        self._user_id = user_id
        self._wallets = dict(wallets) if wallets else {}
        self._user = user 

    # ГЕТТЕРЫ
    @property
    def wallets(self) -> dict[str, "Wallet"]:
        return dict(self._wallets)

    @property
    def user_id(self) -> int:
        return self._user_id
    
    @property
    def user(self) -> "User | None":
        """Объект пользователя"""
        return self._user

    # Публичные методы
    def add_currency(self, currency_code: str) -> "Wallet":
        """Добавляет новый кошелёк (код валюты должен быть уникален)."""
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")

        code = currency_code.strip().upper()
        if code in self._wallets:
            raise ValueError(f"Кошелёк для валюты {code} уже существует")

        wallet = Wallet(code)
        self._wallets[code] = wallet
        return wallet

    def get_total_value(self, base_currency='USD', rates: dict | None = None) -> float:
        """Общая стоимость всех валют в base_currency по фиксированным курсам."""
        base = base_currency.strip().upper()
        effective_rates = rates if rates is not None else self._DEFAULT_RATES

        if base not in effective_rates:
            raise ValueError(f"Нет курса для базовой валюты {base}")
        base_in_usd = effective_rates[base]
        
        total_usd = 0.0
        for code, wallet in self._wallets.items():
            if code not in effective_rates:
                raise ValueError(f"Нет курса для валюты {code}")
            total_usd += wallet.balance * effective_rates[code]
        
        return total_usd / base_in_usd
    
    def get_wallet(self, currency_code: str) -> "Wallet" | None:
        """Возвращает кошелёк по коду валюты (или None, если нет)."""
        if not isinstance(currency_code, str):
            return None
        return self._wallets.get(currency_code.strip().upper())


