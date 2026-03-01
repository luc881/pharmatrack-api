import logging


def get_logger(name: str) -> logging.Logger:
    """
    Retorna un logger bajo el namespace 'pharmatrack'.

    Uso en cualquier módulo:
        from pharmatrack.utils.logger import get_logger
        logger = get_logger(__name__)

        logger.info("Producto creado")
        logger.warning("Stock bajo en producto ID 5")
        logger.error("Error al procesar venta", exc_info=True)
    """
    # Siempre bajo el namespace pharmatrack para que aplique
    # la configuración definida en logging_config.py
    if not name.startswith("pharmatrack"):
        name = f"pharmatrack.{name}"
    return logging.getLogger(name)