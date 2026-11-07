import shlex

import valutatrade_hub.core.usecases as usecases
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    LoginError,
    RegisterError,
    ValutaTradeError,
)

from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import Storage
from valutatrade_hub.parser_service.updater import RatesUpdater
from valutatrade_hub.infra.database import DatabaseManager

# Форматирование
def _fmt_amount(value: float) -> str:
    """Форматирование суммы"""
    if abs(value) >= 1:
        return f"{value:.2f}"
    return f"{value:.4f}"


def _fmt_rate(value: float) -> str:
    """Форматирование курса"""
    if abs(value) >= 1:
        return f"{value:.2f}"
    return f"{value:.8f}".rstrip("0").rstrip(".")


def print_help() -> None:
    """Вывод справки по командам."""
    print("\n*** Пользователи ***")
    print("<command> register --username <name> --password <pass> - регистрация.")
    print("<command> login --username <name> --password <pass> - вход.")

    print("\n*** Портфель ***")
    print("<command> show-portfolio [--base <code>] - портфель и итог.")
    print("<command> buy --currency <code> --amount <num> - купить валюту.")
    print("<command> sell --currency <code> --amount <num> - продать валюту.")

    print("\n*** Курсы ***")
    print("<command> get-rate --from <code> --to <code> - курс одной валюты к другой.")
    print("<command> update-rates [--source coingecko|exchangerate] - обновить курсы.")
    print("<command> show-rates [--currency <code>] [--top <N>] [--base <code>] "
          "- список курсов из кеша.")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы.")
    print("<command> help - справочная информация\n")

# Разбор флагов
def _parse_flags(argv: list[str]) -> dict[str, str]:
    """Разбирает список строк в словарь {флаг:аргумент}"""
    result: dict[str, str] = {}
    i = 0
    while i < len(argv):
        token = argv[i]
        if not token.startswith("--"):
            raise ValueError(f"Ожидался флаг --..., получено: {token!r}")
        key = token[2:]
        if i + 1 >= len(argv):
            raise ValueError(f"Флаг {token} требует значения")
        result[key] = argv[i + 1]
        i += 2
    return result

# Главный цикл 
def run() -> None:
    """Главный цикл программы: ввод команд, выполнение, выход."""
    print_help()

    while True:
        try:
            user_input = input("\n>>>Введите команду: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из программы.")
            break

        if not user_input:
            continue

        try:
            args = shlex.split(user_input)
        except ValueError as e:
            print(f"Ошибка разбора команды: {e}")
            continue

        if not args:
            continue

        command = args[0].lower()

        # <command> exit
        if command == "exit":
            print("Выход из программы.")
            break

        # <command> help
        elif command == "help":
            print_help()

        # <command> register --username <name> --password <pass>
        elif command == "register":
            try:
                flags = _parse_flags(args[1:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue

            if not all((k in flags for k in ("username", "password"))):
                print("Ошибка: register --username <name> --password <pass>")
                continue

            try:
                user = usecases.register_user(username=flags["username"], 
                                              password=flags["password"])
            except RegisterError as e:
                print(e)
                continue

            print(
                f"Пользователь '{user.username}' зарегистрирован "
                f"(id={user.user_id}). "
                f"Войдите: login --username {user.username} --password ****"
            )

        # <command> login --username <name> --password <pass>
        elif command == "login":
            try:
                flags = _parse_flags(args[1:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue

            if not all((k in flags for k in ("username", "password"))):
                print("Ошибка: login --username <name> --password <pass>")
                continue

            try:
                user = usecases.login_user(username=flags["username"], 
                                           password=flags["password"])
            except LoginError as e:
                print(e)
                continue

            print(f"Вы вошли как '{user.username}'")

        # <command> show-portfolio [--base <code>]
        elif command == "show-portfolio":
            try:
                flags = _parse_flags(args[1:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue

            if usecases.get_current_user() is None:
                print("Сначала выполните login")
                continue

            base = flags.get("base", "USD")

            try:
                view = usecases.get_portfolio_view(base_currency=base)
            except ApiRequestError as e:
                print(e)
                print("Повторите попытку позже или проверьте соединение с сетью.")
                continue
            except (ValutaTradeError,ValueError, ) as e:
                print(e)
                continue

            if not view["lines"]:
                print(
                    f"Портфель пользователя '{view['username']}' "
                    f"(база: {view['base']}) пуст."
                )
                continue

            print(
                f"Портфель пользователя '{view['username']}' "
                f"(база: {view['base']}):"
            )
            for line in view["lines"]:
                print(
                    f"- {line['currency_code']}: "
                    f"{_fmt_amount(line['balance'])}  → "
                    f"{_fmt_amount(line['value'])} {view['base']}"
                )
            print("-" * 33)
            print(f"ИТОГО: {(view['total'])} {view['base']}")

        # <command> get-rate --from <code> --to <code>
        elif command == "get-rate":
            try:
                flags = _parse_flags(args[1:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue

            if not all((k in flags for k in ("from", "to"))):
                print("Ошибка: get-rate --from <code> --to <code>")
                continue

            try:
                result = usecases.get_rate(from_code=flags["from"], 
                                           to_code=flags["to"])
            except ApiRequestError as e:
                print(e)
                print("Повторите попытку позже или проверьте соединение с сетью.")
                continue
            except CurrencyNotFoundError as e:
                print(e)
                print("Подсказка: get-rate --from <code> --to <code> "
                      "- курс одной валюты к другой.")
                continue
            except (ValutaTradeError,ValueError, ) as e:
                print(e)
                continue
                
            print(
                f"Курс {result['from']}→{result['to']}: "
                f"{_fmt_rate(result['rate'])} "
                f"(обновлено: {result['updated_at']:%Y-%m-%d %H:%M:%S})"
            )
            print(
                f"Обратный курс {result['to']}→{result['from']}: "
                f"{_fmt_rate(result['back_rate'])}"
            )

        # <command> buy --currency <code> --amount <float>
        elif command == "buy":
            try:
                flags = _parse_flags(args[1:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue
            
            if not all((k in flags for k in ("currency", "amount"))):
                print("Ошибка: buy --currency <code> --amount <float>")
                continue

            amount = flags["amount"]

            try:
                result = usecases.buy_currency(currency_code=flags["currency"], 
                                               amount=float(amount))
            except ApiRequestError as e:
                print(e)
                print("Повторите попытку позже или проверьте соединение с сетью.")
                continue
            except (ValutaTradeError,ValueError) as e:
                print(e)
                continue

            code = result["currency_code"]
            print(
                f"Покупка выполнена: {_fmt_amount(result['amount'])} {code} "
                f"по курсу {_fmt_amount(result['rate'])} USD/{code}"
            )
            print("Изменения в портфеле:")
            print(
                f"- {code}: было {_fmt_amount(result['balance_before'])} → "
                f"стало {_fmt_amount(result['balance_after'])}"
            )
            print(
                f"Оценочная стоимость покупки: "
                f"{_fmt_amount(result['total_value'])} USD"
            )

        # <command> sell --currency <code> --amount <float>
        elif command == "sell":
            try:
                flags = _parse_flags(args[1:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue

            if not all((k in flags for k in ("currency", "amount"))):
                print("Ошибка: sell --currency <code> --amount <float>")
                continue

            amount = flags["amount"]

            try:
                result = usecases.sell_currency(currency_code=flags["currency"], 
                                                amount=float(amount))
            except ApiRequestError as e:
                print(e)
                print("Повторите попытку позже или проверьте соединение с сетью.")
                continue
            except (ValutaTradeError,ValueError, ) as e:
                print(e)
                continue

            code = result["currency_code"]
            print(
                f"Продажа выполнена: {_fmt_amount(result['amount'])} {code} "
                f"по курсу {_fmt_amount(result['rate'])} USD/{code}"
            )
            print("Изменения в портфеле:")
            print(
                f"- {code}: было {_fmt_amount(result['balance_before'])} → "
                f"стало {_fmt_amount(result['balance_after'])}"
            )
            print(
                f"Оценочная выручка: "
                f"{_fmt_amount(result['total_value'])} USD"
            )

        # <command> update-rates [--source coingecko|exchangerate]
        elif command == "update-rates":
            try:
                flags = _parse_flags(args[1:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue

            source = flags.get("source")
            src = (source or "all").strip().lower()

            if src not in ("all", "coingecko", "exchangerate"):
                print(
                    f"Неизвестный источник '{source}'. "
                    f"Допустимо: coingecko, exchangerate"
                )
                continue

            config = ParserConfig()
            clients = []
            if src in ("all", "coingecko"):
                clients.append(CoinGeckoClient(config))
            if src in ("all", "exchangerate"):
                clients.append(ExchangeRateApiClient(config))

            print("INFO: Starting rates update...")

            merged: dict[str, float] = {}
            sources: dict[str, str] = {}
            errors: list[str] = []

            for client in clients:
                name = client.__class__.__name__
                print(f"INFO: Fetching from {name}...", end=" ")
                try:
                    rates = client.fetch_rates()
                except ApiRequestError as e:
                    print(f"ERROR ({e})")
                    errors.append(f"{name}: {e}")
                    continue

                if not rates:
                    print("OK (0 rates)")
                    continue

                print(f"OK ({len(rates)} rates)")
                for pair, rate in rates.items():
                    merged[pair] = float(rate)
                    sources[pair] = name

            if not merged:
                print(
                    "Update completed with errors. "
                    "Check logs/actions.log for details."
                )
                continue

            storage = Storage(config)
            print(f"INFO: Writing {len(merged)} rates to {config.RATES_FILE_PATH}...")
            snapshot = storage.save_snapshot(prices=merged, sources=sources)
            storage.append_history(prices=merged, sources=sources)

            last_refresh = snapshot.get("last_refresh", "-")

            if errors:
                print(
                    "Update completed with errors. "
                    "Check logs/actions.log for details."
                )
            else:
                print(
                    f"Update successful. Total rates updated: {len(merged)}. "
                    f"Last refresh: {last_refresh}"
                )

        # <command> show-rates [--currency <code>] [--top <N>] [--base <code>]
        elif command == "show-rates":
            try:
                flags = _parse_flags(args[1:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue

            db = DatabaseManager()
            rates = db.load_rates()

            # убираем метаданные
            pairs = {
                k: v for k, v in rates.items()
                if k not in ("source", "last_refresh") and isinstance(v, dict)
            }

            if not pairs:
                print(
                    "Локальный кеш курсов пуст. "
                    "Выполните 'update-rates', чтобы загрузить данные."
                )
                continue

            # Фильтр по валюте
            currency_filter = flags.get("currency")
            if currency_filter:
                code = currency_filter.strip().upper()
                filtered = {
                    pair: v for pair, v in pairs.items()
                    if code in pair.split("_")
                }
                if not filtered:
                    print(f"Курс для '{code}' не найден в кеше.")
                    continue
                pairs = filtered

            # Все пары к base
            base_filter = flags.get("base")
            if base_filter:
                base = base_filter.strip().upper()
                filtered = {
                    pair: v for pair, v in pairs.items()
                    if pair.endswith(f"_{base}")
                }
                if not filtered:
                    print(f"Курс для '{base}' не найден в кеше.")
                    continue
                pairs = filtered

            # Сортировка
            top = flags.get("top")
            if top is not None:
                try:
                    top_n = int(top)
                    if top_n <= 0:
                        raise ValueError
                except ValueError:
                    print("Ошибка: --top должно быть положительным целым числом")
                    continue
                # по убыванию курса
                items = sorted(
                    pairs.items(),
                    key=lambda kv: kv[1].get("rate", 0.0),
                    reverse=True,
                )[:top_n]
            else:
                # по алфавиту
                items = sorted(pairs.items(), key=lambda kv: kv[0])

            # Вывод  
            last_refresh = rates.get("last_refresh", "-")
            print(f"Rates from cache (updated at {last_refresh}):")
            for pair, entry in items:
                rate = float(entry.get("rate", 0.0))
                print(f"- {pair}: {_fmt_rate(rate)}")


        else:
            print(f"Команды '{command}' нет. Попробуйте снова.")



