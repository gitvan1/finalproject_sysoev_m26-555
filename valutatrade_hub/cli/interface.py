import shlex

import valutatrade_hub.core.usecases as usecases

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
                user = usecases.register_user(flags["username"], flags["password"])
            except usecases.RegisterError as e:
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
                user = usecases.login_user(flags["username"], flags["password"])
            except usecases.LoginError as e:
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
                view = usecases.get_portfolio_view(base)
            except (usecases.LoginError, 
                    usecases.PortfolioError, 
                    usecases.RateError) as e:
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
                result = usecases.get_rate(flags["from"], flags["to"])
            except usecases.RateError as e:
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

            amount = float(flags["amount"])

            try:
                result = usecases.buy_currency(flags["currency"], amount)
            except (usecases.LoginError, ValueError, usecases.PortfolioError) as e:
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

            amount = float(flags["amount"])

            try:
                result = usecases.sell_currency(flags["currency"], amount)
            except (usecases.LoginError, ValueError, usecases.PortfolioError) as e:
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

        else:
            print(f"Команды '{command}' нет. Попробуйте снова.")



