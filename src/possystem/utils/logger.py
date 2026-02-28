import logging


def get_logger(name: str) -> logging.Logger:
    """
    Retorna un logger bajo el namespace 'possystem'.

    Uso en cualquier módulo:
        from possystem.utils.logger import get_logger
        logger = get_logger(__name__)

        logger.info("Producto creado")
        logger.warning("Stock bajo en producto ID 5")
        logger.error("Error al procesar venta", exc_info=True)
    """
    # Siempre bajo el namespace possystem para que aplique
    # la configuración definida en logging_config.py
    if not name.startswith("possystem"):
        name = f"possystem.{name}"
    return logging.getLogger(name)