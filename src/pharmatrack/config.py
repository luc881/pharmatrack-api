from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # =========================================================
    # 🗄️ Database
    # =========================================================
    database_url: str

    # =========================================================
    # 🔐 JWT / Security
    # =========================================================
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # =========================================================
    # 🌍 App
    # =========================================================
    environment: str = "development"

    # =========================================================
    # 🖼️ Caché local de imágenes (modo offline / convención)
    # =========================================================
    # Carpeta con las imágenes de Cloudinary descargadas por
    # scripts/cache_images.py. Vacío (producción) = feature apagada.
    image_cache_dir: str = ""

    # =========================================================
    # 🔒 CORS
    # =========================================================
    # En producción, setear ALLOWED_ORIGINS en Railway como JSON:
    # ["https://app.opuntiaden.com"]
    # No usar "*" con allow_credentials=True — los browsers lo rechazan.
    allowed_origins: list[str] = [
        "https://app.opuntiaden.com",
        "https://www.opuntiaden.com",
        "https://opuntiaden.com",
    ]

    # =========================================================
    # 📧 Email (Resend)
    # =========================================================
    resend_api_key: str = ""
    # Remitente de todos los correos; el dominio debe estar verificado en
    # Resend o el envío falla (el pedido/venta se guarda igual).
    email_from: str = "noreply@contact.opuntiaden.com"
    frontend_url: str = "https://app.opuntiaden.com"
    # A donde llega el aviso de pedido nuevo. Vacio = no se manda.
    order_notify_email: str = ""

    # =========================================================
    # 👤 Login de clientes con Google (sitio publico)
    # =========================================================
    # Mismo client id que usa Auth.js en pharmatrack-web; el token que manda
    # el sitio solo se acepta si fue emitido para esta aplicacion.
    google_client_id: str = ""
    # URL del sitio publico (links de "ver mi pedido" en los correos)
    site_url: str = "https://www.opuntiaden.com"

    # =========================================================
    # 💳 Pagos en linea (Mercado Pago Checkout Pro)
    # =========================================================
    # Access Token de la aplicacion. Copiar el de PRUEBA para probar sin cobrar
    # y el PRODUCTIVO para cobrar de verdad: ambos empiezan con APP_USR-, la
    # credencial es la que decide el ambiente. Vacio = pagos en linea apagados
    # (503) y todo sigue por link de pago manual.
    mercadopago_access_token: str = ""
    # "Clave secreta" del webhook (panel > Notificaciones > Webhooks). Valida
    # la firma de los avisos antes de consultarlos. Vacio = no se valida (el
    # pago igual se verifica contra la API, que es lo que da la seguridad).
    mercadopago_webhook_secret: str = ""

    # =========================================================
    # 📋 Logging
    # =========================================================
    log_level: str = "DEBUG"
    # WARNING por defecto — silencia las queries de SQLAlchemy
    # Cambia a INFO en .env solo cuando necesites debuggear queries
    sqlalchemy_log_level: str = "WARNING"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    # ✅ Pydantic v2 — reemplaza class Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()