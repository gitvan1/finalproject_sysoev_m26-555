from datetime import datetime

from . import utils
from .constants import (
    CACHE_TTL,
    DEFAULT_RATES,
    META_KEYS,
    PORTFOLIOS_FILE,
    RATES_FILE,
    USERS_FILE,
)
from .models import Portfolio, User, Wallet

# Текущая сессия
_current_user: User | None = None

class RegisterError(Exception):
    """Ошибка бизнес-логики регистрации."""

class LoginError(Exception):
    """Ошибка бизнес-логики входа."""

class PortfolioError(Exception):
    """Бизнес-ошибка портфеля"""

class RateError(Exception):
    """Бизнес-ошибка получения курса."""

def register_user(username: str, password: str) -> User:
    """Регистрирует пользователя и создаёт пустой портфель."""
    # username
    if not isinstance(username, str) or not username.strip():
        raise RegisterError("Имя пользователя не может быть пустым")
    username = username.strip()

    # password
    if not isinstance(password, str) or len(password) < 4:
        raise RegisterError("Пароль должен быть не короче 4 символов")

    # уникальность
    users = utils.load_json(USERS_FILE)
    users = users if users else []
    if any(u["username"].lower() == username.lower() for u in users):
        raise RegisterError(f"Имя пользователя '{username}' уже занято")

    # user_id (автоинкремент)
    new_id = utils.next_user_id(users)

    # создание пользователя и хеширование пароля
    user = User(user_id=new_id, username=username)
    user.change_password(password)

    # добавление в users.json
    users.append(user.to_dict())
    utils.save_json(USERS_FILE, users)

    # пустой портфель
    portfolios = utils.load_json(PORTFOLIOS_FILE)
    portfolios.append({"user_id": new_id, "wallets": {}})
    utils.save_json(PORTFOLIOS_FILE, portfolios)

    return user

def login_user(username: str, password: str) -> User:
    """Вход в систему: ищет пользователя по username и сверяет пароль."""

    global _current_user
    # поиск
    if not isinstance(username, str) or not username.strip():
        raise LoginError("Имя пользователя не может быть пустым")
    username = username.strip()

    users = utils.load_json(USERS_FILE)
    data = None
    for u in users:
        if u["username"].lower() == username.lower():
            data = u
            break
    if data is None:
        raise LoginError(f"Пользователь '{username}' не найден")

    # проверка пароля
    user = User.from_dict(data)
    if not user.verify_password(password):
        raise LoginError("Неверный пароль")

    # сессия
    _current_user = user
    return user

def get_current_user() -> User | None:
    """Возвращает текущего залогиненного пользователя или None."""
    return _current_user

def get_current_portfolio() -> Portfolio:
    """Портфель текущего пользователя."""
    user = get_current_user()
    if user is None:
        raise LoginError("Сначала выполните login")
    
    portfolios = utils.load_json(PORTFOLIOS_FILE)

    data = None
    for p in portfolios:
        if p["user_id"] == user.user_id:
            data = p
            break
    if data is None:
        return Portfolio(user_id=user.user_id, wallets={}, user=user)

    wallets = {
        code: Wallet.from_dict({"currency_code": code, **w})
        for code, w in data.get("wallets", {}).items()
    }
    return Portfolio(user_id=user.user_id, wallets=wallets, user=user)

def get_portfolio_view(base_currency: str = "USD") -> dict:
    """Готовит данные для show-portfolio"""
    portfolio = get_current_portfolio()
    rates = _get_rates()
    base = base_currency.strip().upper()

    currencies = {
        c for k in rates if k not in META_KEYS for c in k.split("_")
    }
    if base not in currencies:
        raise PortfolioError(f"Неизвестная базовая валюта '{base}'")

    lines = []
    for code, wallet in portfolio.wallets.items():
        if code == base:
            value = wallet.balance 
        elif f"{code}_{base}" in rates:
            value = wallet.balance * rates[f"{code}_{base}"]["rate"]
        elif f"{base}_{code}" in rates:
            value = wallet.balance / rates[f"{base}_{code}"]["rate"]
        else:
            continue
        lines.append({
            "currency_code": code,
            "balance": wallet.balance,
            "value": value,
        })

    total = sum(line["value"] for line in lines)

    return {
        "username": portfolio.user.username if portfolio.user else "?",
        "base": base,
        "lines": lines,
        "total": total,
    }

def _save_portfolio(portfolio: Portfolio) -> None:
    """Заменяет/добавляет запись портфеля в portfolios.json."""
    all_portfolios = utils.load_json(PORTFOLIOS_FILE)
    for i, p in enumerate(all_portfolios):
        if p["user_id"] == portfolio.user_id:
            all_portfolios[i] = portfolio.to_dict()
            break
    else:
        all_portfolios.append(portfolio.to_dict())
    utils.save_json(PORTFOLIOS_FILE, all_portfolios)

def buy_currency(currency_code: str, amount: float) -> dict:
    """Покупка валюты: увеличивает баланс кошелька (создаёт, если нет)."""
    # Логин
    user = get_current_user()
    if user is None:
        raise LoginError("Сначала выполните login")

    # Валидация currency
    if not isinstance(currency_code, str) or not currency_code.strip():
        raise ValueError("'currency' должен быть непустой строкой")
    code = currency_code.strip().upper()

    # Валидация amount
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("'amount' должен быть положительным числом")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    amount = float(amount)

    # Загрузка портфеля
    portfolio = get_current_portfolio()

    # Курс
    try:
        rate = get_rate(currency_code, "USD")["rate"]
    except (RateError):
        raise PortfolioError(f"Не удалось получить курс для {code}→USD")

    # Изменение портфеля
    wallet = portfolio.get_wallet(code)
    if wallet is None:
        wallet = portfolio.add_currency(code)
    balance_before = wallet.balance
    wallet.deposit(amount)
    balance_after = wallet.balance

    # Сохранение portfolios.json
    _save_portfolio(portfolio)

    return {
        "username": user.username,
        "currency_code": code,
        "amount": amount,
        "rate": rate,
        "balance_before": balance_before,
        "balance_after": balance_after,
        "total_value": amount * rate,
    }

def sell_currency(currency_code: str, amount: float) -> dict:
    """Продажа валюты: уменьшает баланс кошелька"""

    # Логин
    user = get_current_user()
    if user is None:
        raise LoginError("Сначала выполните login")

    # Валидация currency
    if not isinstance(currency_code, str) or not currency_code.strip():
        raise ValueError("'currency' должен быть непустой строкой")
    code = currency_code.strip().upper()

    # Валидация amount
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("'amount' должен быть положительным числом")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    amount = float(amount)

    # Портфель
    portfolio = get_current_portfolio()

    # 5. Кошелёк должен существовать
    wallet = portfolio.get_wallet(code)
    if wallet is None:
        raise PortfolioError(
            f"У вас нет кошелька '{code}'. "
            f"Добавьте валюту: она создаётся автоматически при первой покупке."
        )

    # Достаточно средств
    if wallet.balance < amount:
        raise PortfolioError(
            f"Недостаточно средств: доступно {wallet.balance} {code}, "
            f"требуется {amount} {code}"
        )

    # Курс
    try:
        rate = get_rate(currency_code, "USD")["rate"]
    except (RateError):
        raise PortfolioError(f"Не удалось получить курс для {code}→USD")

    # Изменение портфеля
    balance_before = wallet.balance
    wallet.withdraw(amount)
    balance_after = wallet.balance

    # Сохранение
    _save_portfolio(portfolio)

    return {
        "username": user.username,
        "currency_code": code,
        "amount": amount,
        "rate": rate,
        "balance_before": balance_before,
        "balance_after": balance_after,
        "total_value": amount * rate,
    }

def _rates_fresh(data: dict) -> bool:
    """Все записи в кеше свежее CACHE_TTL."""
    rates_data = {k: v for k, v in data.items() if k not in META_KEYS}
    if not rates_data:
        return False
    now = datetime.now()
    for rate in rates_data.values():
        try:
            updated = datetime.fromisoformat(rate["updated_at"])
        except (KeyError, ValueError, TypeError):
            return False
        if now - updated > CACHE_TTL:
            return False
    return True


def _save_rates(prices: dict[str, dict], source: str = "ParserService") -> dict:
    """Обновляет rates.json единой меткой времени, возвращает записанное."""
    now = datetime.now().isoformat(timespec="seconds")

    data = {}
    for code, price in prices.items():
        if code not in META_KEYS:
            data[code] = {"rate": float(price["rate"]), "updated_at": now}
    data["source"] = source
    data["last_refresh"] = now
    utils.save_json(RATES_FILE, data)
    return data

def _get_rates() -> dict:
    """Получает актуальные курсы"""
    rates = utils.load_json(RATES_FILE)
    if isinstance(rates, dict) and _rates_fresh(rates):
        return rates
    
    # Позже будет реализован парсер
    # Сейчас заглушка
    prices = DEFAULT_RATES
    return _save_rates(prices)

def get_rate(from_code: str, to_code: str) -> dict:
    """Курс from_code → to_code + обратный, с меткой времени."""

    if not isinstance(from_code, str) or not from_code.strip():
        raise RateError("Код исходной валюты не может быть пустым")
    if not isinstance(to_code, str) or not to_code.strip():
        raise RateError("Код целевой валюты не может быть пустым")
    
    frm = from_code.strip().upper()
    to = to_code.strip().upper()

    try:
        rates = _get_rates()
    except Exception:
        raise RateError(
            f"Курс {frm}→{to} недоступен. Повторите попытку позже."
        )
    

    if frm == to:
        to_frm, frm_to = 1.0, 1.0
        updated = rates.get("last_refresh")
    elif f"{frm}_{to}" in rates:
        frm_to = rates[f"{frm}_{to}"]["rate"]
        to_frm = 1 / frm_to
        updated = rates[f"{frm}_{to}"]["updated_at"]
    elif f"{to}_{frm}" in rates:
        to_frm = rates[f"{to}_{frm}"]["rate"]
        frm_to = 1 / to_frm
        updated = rates[f"{to}_{frm}"]["updated_at"]
    else:
        raise RateError(
            f"Курс {frm}→{to} недоступен. Повторите попытку позже."
        )
    
    try:
        updated_at = (
            datetime.fromisoformat(updated)
            if updated else datetime.now()
        )
    except (ValueError, TypeError):
        updated_at = datetime.now()

    return {
        "from": frm,
        "to": to,
        "rate": frm_to,
        "back_rate": to_frm,
        "updated_at": updated_at,

    }