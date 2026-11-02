import os
from datetime import timedelta
import valutatrade_hub.infra.settings as settings

_settings_loader = settings.SettingsLoader()
# путь к папке data
_data_dir = _settings_loader.get("data_dir")
DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", _data_dir)
)

# пути к файлам
_users_file = _settings_loader.get("users_file")
_portfolios_file = _settings_loader.get("portfolios_file")
_rates_file = _settings_loader.get("rates_file")

USERS_FILE = os.path.join(DATA_DIR, _users_file)
PORTFOLIOS_FILE = os.path.join(DATA_DIR, _portfolios_file)
RATES_FILE = os.path.join(DATA_DIR, _rates_file)

# время жизни курса валют
_rates_ttl = _settings_loader.get("rates_ttl_seconds")
CACHE_TTL = timedelta(seconds=_rates_ttl)

# «мета‑ключи» для rates.json
META_KEYS = frozenset({"source", "last_refresh"})

# Фиксированные курсы (заглушка)
DEFAULT_RATES: dict[str, dict] = {
"EUR_USD": {"rate": 1.0786,    "updated_at": "2026-01-01T00:00:00"},
"BTC_USD": {"rate": 59337.21,  "updated_at": "2026-01-01T00:00:00"},
"RUB_USD": {"rate": 0.01016,   "updated_at": "2026-01-01T00:00:00"},
"ETH_USD": {"rate": 3720.00,   "updated_at": "2026-01-01T00:00:00"},
}

# Базовая валюта
BASE_CURRENCY = _settings_loader.get("base_currency")