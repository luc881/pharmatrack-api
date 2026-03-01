import logging
import logging.config
from pathlib import Path
from possystem.config import settings


def setup_logging() -> None:
    """
    Configura el sistema de logging de la aplicación.
    - Desarrollo : logs en consola + archivo logs/app.log
    - Producción : logs solo en consola, sin archivo

    Para ver queries de SQLAlchemy temporalmente:
        Agrega SQLALCHEMY_LOG_LEVEL=INFO en tu .env
        Al terminar de debuggear, elimina la variable o vuelve a WARNING
    """

    log_level = settings.log_level.upper()
    sqlalchemy_log_level = settings.sqlalchemy_log_level.upper()

    fmt_detailed = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # =========================================================
    # 🔹 Handlers
    # =========================================================
    handlers: dict = {
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "detailed",
            "stream": "ext://sys.stdout",
        }
    }

    if not settings.is_production:
        logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)

        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(logs_dir / "app.log"),
            "maxBytes": 5 * 1024 * 1024,  # 5 MB
            "backupCount": 3,
            "encoding": "utf-8",
        }

    active_handlers = list(handlers.keys())

    # =========================================================
    # 🔹 Configuración
    # =========================================================
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {"format": fmt_detailed},
        },
        "handlers": handlers,
        "loggers": {
            # 🔹 Tu aplicación
            "possystem": {
                "level": log_level,
                "handlers": active_handlers,
                "propagate": False,
            },
            # 🔹 SQLAlchemy — WARNING por defecto, INFO solo cuando debuggeas
            "sqlalchemy.engine": {
                "level": sqlalchemy_log_level,
                "handlers": active_handlers,
                "propagate": False,
            },
            # 🔹 Alembic
            "alembic": {
                "level": "INFO",
                "handlers": active_handlers,
                "propagate": False,
            },
            # 🔹 Uvicorn
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
        "root": {
            "level": "WARNING",
            "handlers": active_handlers,
        },
    }

    logging.config.dictConfig(config)