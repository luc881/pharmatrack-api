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
    # ["https://app.farmaciaselene.com"]
    # No usar "*" con allow_credentials=True — los browsers lo rechazan.
    allowed_origins: list[str] = [
        "https://app.farmaciaselene.com",
        "https://www.farmaciaselene.com",
        "https://farmaciaselene.com",
    ]

    # =========================================================
    # 📧 Email (Resend)
    # =========================================================
    resend_api_key: str = ""
    frontend_url: str = "https://pharmatrack-frontend.vercel.app"
    # A donde llega el aviso de pedido nuevo. Vacio = no se manda.
    order_notify_email: str = ""

    # =========================================================
    # 👤 Login de clientes con Google (sitio publico)
    # =========================================================
    # Mismo client id que usa Auth.js en pharmatrack-web; el token que manda
    # el sitio solo se acepta si fue emitido para esta aplicacion.
    google_client_id: str = ""
    # URL del sitio publico (links de "ver mi pedido" en los correos)
    site_url: str = "https://www.farmaciaselene.com"

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