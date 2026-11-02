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
    "log_format": "...",
    "log_level": "INFO",
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