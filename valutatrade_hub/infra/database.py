import json
import os
import tempfile

from .settings import SettingsLoader


class DatabaseManager:
    """Singleton-обёртка над JSON-файлами."""

    _instance: "DatabaseManager | None" = None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._settings = SettingsLoader()
        self._initialized = True

    # Чтение
    def load(self, path: str, default=None):
        """Читает JSON."""
        if not os.path.exists(path):
            return [] if default is None else default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return [] if default is None else default

    # Запись 
    def save(self, path: str, data) -> None:
        """Атомарная запись JSON через tempfile."""
        directory = os.path.dirname(path) or "."
        os.makedirs(directory, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=os.path.basename(path) + ".",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=4)
            tmp_path = tmp.name

        try:
            os.replace(tmp_path, path)
        except OSError:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def load_users(self):
        return self.load(self._settings.users_file, default=[])

    def save_users(self, users) -> None:
        self.save(self._settings.users_file, users)

    def load_portfolios(self):
        return self.load(self._settings.portfolios_file, default=[])

    def save_portfolios(self, portfolios) -> None:
        self.save(self._settings.portfolios_file, portfolios)

    def load_rates(self) -> dict:
        data = self.load(self._settings.rates_file, default={})
        return data if isinstance(data, dict) else {}

    def save_rates(self, rates: dict) -> None:
        self.save(self._settings.rates_file, rates)