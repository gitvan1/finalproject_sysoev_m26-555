import os
import tomllib

_DEFAULTS = {
    "data_dir": "data",
    "users_file": "users.json",
    "portfolios_file": "portfolios.json",
    "rates_file": "rates.json",
    "rates_ttl_seconds": 300,
    "base_currency": "USD",
    "log_file": "logs/actions.log",
    "log_level": "INFO",
    "log_max_bytes": 1000000,
    "log_backup_count": 3
}

class SettingsLoader:
    """
    Singleton-загрузчик конфигурации.

    Выбран способ через __new__ (а не метакласс):
    - проще читать и отлаживать — один класс, один метод;
    - не нужен отдельный класс-метакласс ради одной задачи.
    """

    _instance: "SettingsLoader | None" = None

    def __new__(cls) -> "SettingsLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        # Инициализация выполняется один раз — при первом создании.
        # При повторном SettingsLoader() __new__ вернёт _instance,
        # а __init__ снова вызовется, поэтому защищаемся флагом _initialized.
        if getattr(self, "_initialized", False):
            return
        self._project_root = self._find_project_root()
        self._config: dict = {}
        self.reload()
        self._initialized = True

    # Публичный интерфейс 
    def get(self, key: str, default = None):
        """Возвращает значение ключа."""
        if key in self._config:
            return self._config[key]
        return default if default is not None else _DEFAULTS.get(key)

    def reload(self) -> "SettingsLoader":
        """Перечитывает pyproject.toml. Возвращает self."""
        self._config = {}

        # pyproject.toml: [tool.valutatrade]
        pyproject_path = os.path.join(self._project_root, "pyproject.toml")
        if os.path.exists(pyproject_path):
            try:
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                section = data.get("tool", {}).get("valutatrade", {})
                if isinstance(section, dict):
                    self._config.update(section)
            except (OSError, tomllib.TOMLDecodeError):
                pass
        return self

    @staticmethod
    def _find_project_root() -> str:
        return os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
    
    @property
    def log_file(self) -> str:
        path = self.get("log_file") or "logs/actions.log"
        if not os.path.isabs(path):
            path = os.path.join(self._project_root, path)
        return os.path.abspath(path)

    @property
    def project_root(self) -> str:
        return self._project_root

    @property
    def data_dir(self) -> str:
        path = self.get("data_dir")
        if not isinstance(path, str) or not path:
            path = "data"
        if not os.path.isabs(path):
            path = os.path.join(self._project_root, path)
        return os.path.abspath(path)

    @property
    def users_file(self) -> str:
        return self._resolve(self.get("users_file"), "users.json")

    @property
    def portfolios_file(self) -> str:
        return self._resolve(self.get("portfolios_file"), "portfolios.json")

    @property
    def rates_file(self) -> str:
        return self._resolve(self.get("rates_file"), "rates.json")

    @property
    def rates_ttl_seconds(self) -> int:
        try:
            return int(self.get("rates_ttl_seconds") or 300)
        except (TypeError, ValueError):
            return 300

    @property
    def base_currency(self) -> str:
        return str(self.get("base_currency") or "USD").upper()

    def _resolve(self, path: object, default_name: str) -> str:
        """Собирает абсолютный путь: data_dir/<path> или data_dir/<default_name>."""
        if not isinstance(path, str) or not path:
            return os.path.join(self.data_dir, default_name)
        if not os.path.isabs(path):
            path = os.path.join(self.data_dir, path)
        return os.path.abspath(path)