# ValutaTrade Hub

Платформа для управления портфелем фиатных и крипто-валют: регистрация,
кошельки, покупка/продажа, актуальные курсы. Состоит из двух сервисов:
**Core Service** (CLI, портфель, сделки) и **Parser Service** (сбор курсов
из CoinGecko и ExchangeRate-API в локальный кеш).

---

## Возможности

- **Пользователи**: регистрация и вход, пароли — SHA-256 с солью.
- **Портфель**: несколько кошельков, покупка/продажа с проверкой остатка,
  просмотр в базовой валюте.
- **Курсы**: два источника — CoinGecko (крипта) и ExchangeRate-API (фиат),
  единый формат пар.
- **Кеш**: `data/rates.json` с TTL (5 минут), автообновление при устаревании.
- **Устойчивость**: сбой одного источника не ломает обновление; при полном
  сбое API используется устаревший кеш; атомарная запись JSON.
- **Parser Service**: ручной (`update-rates`), программный (`run_update()`)
  и фоновый (`scheduler.py`) запуск; история в `exchange_rates.json`.
- **Логи**: аудит действий в `logs/actions.log` с ротацией.
- **Конфигурация**: `SettingsLoader` (`pyproject.toml`),
  API-ключ не хранится в коде.

---

## Структура

```text
finalproject_sysoev_m26-555/
├── data/
│ ├── users.json # пользователи
│ ├── portfolios.json # портфели и кошельки
│ ├── rates.json # снимок курсов (кеш для Core)
│ └── exchange_rates.json # история замеров (Parser)
├── valutatrade_hub/
│ ├── logging_config.py # setup_logging()
│ ├── decorators.py # @log_action
│ ├── core/
│ │ ├── currencies.py # Currency(ABC), Fiat, Crypto, реестр
│ │ ├── exceptions.py # исключения
│ │ ├── models.py # User, Wallet, Portfolio
│ │ ├── usecases.py # бизнес-логика
│ │ └── utils.py 
│ ├── infra/
│ │ ├── settings.py # SettingsLoader (Singleton)
│ │ └── database.py # DatabaseManager (Singleton, атомарная запись)
│ ├── parser_service/
│ │ ├── config.py # ParserConfig
│ │ ├── api_clients.py # CoinGeckoClient, ExchangeRateApiClient
│ │ ├── updater.py # RatesUpdater
│ │ ├── storage.py # rates.json + exchange_rates.json
│ │ └── scheduler.py # периодический запуск
│ └── cli/
│ └── interface.py # run() — команды CLI
├── main.py
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## Установка

Python 3.12+, `uv`.

```bash
uv sync
```

## Запуск

```bash
export EXCHANGERATE_API_KEY=your_key     # для фиата (EUR/GBP/RUB)
uv run python main.py
```

# Команды ValutaTrade Hub

Все команды вводятся в интерактивном CLI (`python main.py`). После запуска
программа показывает приглашение `>>>Введите команду:` и ждёт ввод.

- `help` — справка по всем командам
- `exit` — выход
- Коды валют регистронезависимы: `usd` → `USD`
- Команды `show-portfolio`, `buy`, `sell` требуют `login`

---

## Сводная таблица

| Команда | Аргументы | Логин | Назначение |
|---|---|---|---|
| `register` | `--username --password` | — | Регистрация |
| `login` | `--username --password` | — | Вход |
| `show-portfolio` | `[--base USD]` | + | Портфель и итог |
| `buy` | `--currency --amount` | + | Покупка |
| `sell` | `--currency --amount` | + | Продажа |
| `get-rate` | `--from --to` | — | Курс пары |
| `update-rates` | `[--source coingecko\|exchangerate]` | — | Обновить кеш |
| `show-rates` | `[--currency] [--top N] [--base]` | — | Курсы из кеша |
| `help` | — | — | Справка |
| `exit` | — | — | Выход |

## Пример команд CLI

```text
> register --username alice --password 1234
Пользователь 'alice' зарегистрирован (id=1). Войдите: login --username alice --password ****

> login --username alice --password 1234
Вы вошли как 'alice'

> buy --currency BTC --amount 0.05
Покупка выполнена: 0.0500 BTC по курсу 59,337.21 USD/BTC
Изменения в портфеле:
- BTC: было 0.0000 → стало 0.0500
Оценочная стоимость покупки: 2,966.86 USD

> show-portfolio
Портфель пользователя 'alice' (база: USD):
- BTC: 0.0500  → 2,966.86 USD
---------------------------------
ИТОГО: 2,966.86 USD

> get-rate --from USD --to BTC
Курс USD→BTC: 0.00001685 (обновлено: 2026-11-06 12:00:00)
Обратный курс BTC→USD: 59337.21

> sell --currency BTC --amount 0.01
Продажа выполнена: 0.0100 BTC по курсу 59,337.21 USD/BTC
Изменения в портфеле:
- BTC: было 0.0500 → стало 0.0400
Оценочная выручка: 593.37 USD

> update-rates
INFO: Starting rates update...
INFO: Fetching from CoinGeckoClient... OK (3 rates)
INFO: Fetching from ExchangeRateApiClient... OK (3 rates)
INFO: Writing 6 rates to data/rates.json...
Update successful. Total rates updated: 6. Last refresh: 2026-11-06T12:00:00+00:00

> show-rates --top 2
Rates from cache (updated at 2026-11-06T12:00:00+00:00):
- BTC_USD: 59337.21
- ETH_USD: 3200.00

> exit
Выход из программы.
```
---

## Parser Service

Отдельный микросервис, который собирает курсы из CoinGecko и ExchangeRate-API
и пишет их в `data/rates.json` (снимок) и `data/exchange_rates.json` (история).

### Когда работает

- **Вручную** — по команде `update-rates`.
- **В фоне** — если запущен `scheduler.py`.
- **Автоматически** — при `get-rate`/`show-portfolio`, если `rates.json` старше TTL
  (по умолчанию 5 минут). Core Service сам вызывает `RatesUpdater.run_update()`.

### Ключ
CoinGecko работает без ключа. Для фиата (EUR/GBP/RUB) нужен EXCHANGERATE_API_KEY:

```text
export EXCHANGERATE_API_KEY=your_key
```

## Демонстрация
https://asciinema.org/a/XnGUQEaj6KbBHbZH