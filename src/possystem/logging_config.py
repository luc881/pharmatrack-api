import logging
import logging.config
from pathlib import Path
from possystem.config import settings


def setup_logging() -> None:
    """
    Configura el sistema de logging de la aplicación.
    - Desarrollo : logs en consola (DEBUG) + archivo logs/app.log
    - Producción : logs solo en consola (INFO), sin archivo
    """

    log_level = settings.log_level.upper()

    # =========================================================
    # 🔹 Formato de los mensajes
    # =========================================================
    fmt_detailed = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    fmt_simple   = "%(levelname)-8s | %(name)s | %(message)s"

    # =========================================================
    # 🔹 Handlers disponibles
    # =========================================================
    handlers: dict = {
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "detailed",
            "stream": "ext://sys.stdout",
        }
    }

    # En desarrollo también guardamos logs en archivo
    if not settings.is_production:
        logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)

        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(logs_dir / "app.log"),
            "maxBytes": 5 * 1024 * 1024,  # 5 MB por archivo
            "backupCount": 3,              # guarda hasta 3 archivos anteriores
            "encoding": "utf-8",
        }

    active_handlers = list(handlers.keys())

    # =========================================================
    # 🔹 Configuración completa
    # =========================================================
    config = {
        "version": 1,
        "disable_existing_loggers": False,  # no silencia librerías externas
        "formatters": {
            "detailed": {"format": fmt_detailed},
            "simple":   {"format": fmt_simple},
        },
        "handlers": handlers,
        "loggers": {
            # 🔹 Tu aplicación — nivel configurable desde .env
            "possystem": {
                "level": log_level,
                "handlers": active_handlers,
                "propagate": False,
            },
            # 🔹 SQLAlchemy — solo warnings en producción, queries en desarrollo
            "sqlalchemy.engine": {
                "level": "INFO" if not settings.is_production else "WARNING",
                "handlers": active_handlers,
                "propagate": False,
            },
            # 🔹 Alembic
            "alembic": {
                "level": "INFO",
                "handlers": active_handlers,
                "propagate": False,
            },
            # 🔹 Uvicorn — acceso HTTP
            "uvicorn.access": {
                "level": "INFO",
                "handlers": active_handlers,
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": active_handlers,
                "propagate": False,
            },
        },
        # 🔹 Root logger — captura todo lo que no está definido arriba
        "root": {
            "level": "WARNING",
            "handlers": active_handlers,
        },
    }

    logging.config.dictConfig(config)