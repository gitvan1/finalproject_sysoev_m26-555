# «мета‑ключи» для rates.json
META_KEYS = frozenset({"source", "last_refresh"})

# Фиксированные курсы (заглушка)
DEFAULT_RATES: dict[str, dict] = {
"EUR_USD": {"rate": 1.0786,    "updated_at": "2026-01-01T00:00:00"},
"BTC_USD": {"rate": 59337.21,  "updated_at": "2026-01-01T00:00:00"},
"RUB_USD": {"rate": 0.01016,   "updated_at": "2026-01-01T00:00:00"},
"ETH_USD": {"rate": 3720.00,   "updated_at": "2026-01-01T00:00:00"},
}