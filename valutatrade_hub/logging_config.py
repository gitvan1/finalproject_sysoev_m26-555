import logging
import logging.handlers
import os

from .infra.settings import SettingsLoader

_configured = False

def setup_logging() -> None:
    """Настраивает root logger: файл с ротацией, уровень и формат из настроек."""
    global _configured
    if _configured:
        return

    settings = SettingsLoader()

    log_path = settings.log_file
    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)

    level = getattr(logging, str(settings.get("log_level") or "INFO").upper(), 
                    logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=int(settings.get("log_max_bytes") or 1_000_000),
        backupCount=int(settings.get("log_backup_count") or 3),
        encoding="utf-8",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    _configured = True