"""Modo offline: caché local de imágenes de Cloudinary (IMAGE_CACHE_DIR)."""
from urllib.parse import quote

from fastapi import status

from pharmatrack.config import settings
from pharmatrack.api.routes.image_cache import cache_filename

from .utils import client
from .test_animals import _make_taxonomy, _create_animal

CLOUD_URL = "https://res.cloudinary.com/demo/image/upload/v1/tarantula.jpg"


def test_rewrite_and_serve_cached_image(auth_headers, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "image_cache_dir", str(tmp_path))

    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"], image=CLOUD_URL)

    # El middleware reescribe la URL de Cloudinary hacia el endpoint local
    row = next(
        a for a in client.get("/api/v1/public/animals").json()["data"]
        if a["id"] == animal["id"]
    )
    assert "/api/v1/image-cache?u=" in row["image"]
    assert quote(CLOUD_URL, safe="") in row["image"]

    # Sin archivo cacheado: redirige al original (online sigue funcionando)
    res = client.get(f"/api/v1/image-cache?u={quote(CLOUD_URL, safe='')}", follow_redirects=False)
    assert res.status_code in (status.HTTP_302_FOUND, status.HTTP_307_TEMPORARY_REDIRECT)
    assert res.headers["location"] == CLOUD_URL

    # Con archivo cacheado: lo sirve directo (offline)
    (tmp_path / cache_filename(CLOUD_URL)).write_bytes(b"fake-jpg")
    res = client.get(f"/api/v1/image-cache?u={quote(CLOUD_URL, safe='')}")
    assert res.status_code == status.HTTP_200_OK
    assert res.content == b"fake-jpg"

    # URLs ajenas a Cloudinary: rechazadas (no somos un redirector abierto)
    res = client.get(f"/api/v1/image-cache?u={quote('https://evil.com/x.jpg', safe='')}", follow_redirects=False)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_no_rewrite_when_cache_disabled(auth_headers):
    # settings.image_cache_dir vacío (producción): la URL viaja intacta
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"], image=CLOUD_URL)

    row = next(
        a for a in client.get("/api/v1/public/animals").json()["data"]
        if a["id"] == animal["id"]
    )
    assert row["image"] == CLOUD_URL
