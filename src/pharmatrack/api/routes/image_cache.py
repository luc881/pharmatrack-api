"""Modo offline: sirve imágenes de Cloudinary desde una caché local.

Activo solo cuando IMAGE_CACHE_DIR está definido (el stack local lo setea;
Railway no, así que en producción nada de esto cambia el comportamiento).

- El middleware reescribe las URLs de Cloudinary en las respuestas JSON
  hacia GET /api/v1/image-cache?u=<url original>.
- El endpoint sirve el archivo cacheado si existe; si no, redirige a la
  URL original (con internet todo sigue funcionando igual).
"""

import re
import hashlib
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ...config import settings

CLOUDINARY_PREFIX = "https://res.cloudinary.com/"
_CLOUDINARY_RE = re.compile(rb'https://res\.cloudinary\.com/[^"\\]+')

router = APIRouter(prefix="/image-cache", tags=["Health Check"])


def cache_filename(url: str) -> str:
    """Nombre determinista del archivo cacheado: sha1(url) + extensión."""
    ext = Path(url.split("?")[0]).suffix or ".jpg"
    return hashlib.sha1(url.encode()).hexdigest() + ext


# Sin auth: las imágenes se cargan vía <img src>, que no manda el token.
# Solo acepta URLs de Cloudinary para no ser un redirector abierto.
@router.get("", summary="Imagen cacheada para modo offline")
def get_cached_image(u: str):
    if not u.startswith(CLOUDINARY_PREFIX):
        raise HTTPException(status_code=404, detail="URL no permitida")

    if settings.image_cache_dir:
        path = Path(settings.image_cache_dir) / cache_filename(u)
        if path.is_file():
            return FileResponse(path)

    return RedirectResponse(u)


class ImageCacheRewriteMiddleware(BaseHTTPMiddleware):
    """Reescribe URLs de Cloudinary en respuestas JSON hacia la caché local."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)

        if (
            not settings.image_cache_dir
            or request.method != "GET"
            or "application/json" not in response.headers.get("content-type", "")
        ):
            return response

        body = b"".join([chunk async for chunk in response.body_iterator])

        # base_url respeta el host con el que entró la petición
        # (localhost o la IP del hotspot desde el teléfono)
        base = str(request.base_url).rstrip("/").encode()

        def _rewrite(match):
            original = match.group(0).decode()
            return base + b"/api/v1/image-cache?u=" + quote(original, safe="").encode()

        new_body = _CLOUDINARY_RE.sub(_rewrite, body)

        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(
            content=new_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )
