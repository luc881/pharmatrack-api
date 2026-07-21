"""Verificación del ID token de Google (login de clientes del sitio público).

ponytail: usa el endpoint tokeninfo de Google en vez de traer las llaves
públicas y validar la firma a mano — es el propio Google quien valida, son
diez líneas y el login pasa una sola vez por sesión. Si algún día el volumen
de logins hace pesar el viaje extra, cambiar a JWKS cacheado.
"""
import httpx
from fastapi import HTTPException
from starlette import status

from pharmatrack.config import settings
from pharmatrack.utils.logger import get_logger

logger = get_logger(__name__)

TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
_VALID_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


def expected_client_id() -> str:
    """El client id configurado, limpio de espacios/comillas que se cuelan
    al pegarlo en el panel de variables (causa real de un aud mismatch)."""
    return settings.google_client_id.strip().strip("'\"").strip()


def verify_google_id_token(id_token: str) -> dict:
    """Devuelve {sub, email, name, picture} o lanza 401. Nunca confía en el
    contenido sin comprobar que el token fue emitido PARA esta aplicación."""
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Google sign-in failed.",
    )

    if not expected_client_id():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured.",
        )

    try:
        response = httpx.get(TOKENINFO_URL, params={"id_token": id_token}, timeout=10)
    except httpx.HTTPError as exc:
        logger.error("tokeninfo request failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Could not reach Google.") from exc

    if response.status_code != 200:
        raise invalid

    data = response.json()

    # aud: el token debe haber sido emitido para NUESTRO client id, si no
    # cualquier token de Google de otra app valdría aquí.
    # expected_client_id() tolera espacios/comillas pegados en la variable;
    # el client id es público (va en cada URL de login), se puede loggear.
    expected = expected_client_id()
    if data.get("aud") != expected:
        logger.warning("Google id_token aud mismatch: got=%s expected=%s",
                       data.get("aud"), expected)
        raise invalid
    if data.get("iss") not in _VALID_ISSUERS:
        raise invalid
    # email_verified llega como "true"/"false" (string) desde tokeninfo
    if str(data.get("email_verified", "")).lower() != "true" or not data.get("email"):
        raise invalid

    return {
        "sub": data["sub"],
        "email": data["email"].lower(),
        "name": data.get("name"),
        "picture": data.get("picture"),
    }
