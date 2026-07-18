"""Descarga a disco todas las imágenes de Cloudinary referidas en la BD.

Uso (con DATABASE_URL apuntando a la BD local e IMAGE_CACHE_DIR definido):

    poetry run python -m pharmatrack.scripts.cache_images

Lo llama scripts/sync-down.ps1 después de restaurar la BD, para que el
POS funcione sin internet mostrando las fotos ya existentes.
"""

from pathlib import Path

import httpx
from sqlalchemy import create_engine, text

from pharmatrack.config import settings
from pharmatrack.api.routes.image_cache import CLOUDINARY_PREFIX, cache_filename

# Todas las columnas que guardan URLs de imágenes
QUERIES = [
    "SELECT image FROM animals WHERE image IS NOT NULL",
    "SELECT url FROM animal_photos",
    "SELECT image FROM products WHERE image IS NOT NULL",
]


def main() -> None:
    cache_dir = Path(settings.image_cache_dir or "image_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine(settings.database_url)
    urls: set[str] = set()
    with engine.connect() as conn:
        for query in QUERIES:
            urls.update(row[0] for row in conn.execute(text(query)))

    urls = {u for u in urls if u and u.startswith(CLOUDINARY_PREFIX)}

    downloaded = skipped = failed = 0
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for url in sorted(urls):
            target = cache_dir / cache_filename(url)
            if target.is_file():
                skipped += 1
                continue
            try:
                response = client.get(url)
                response.raise_for_status()
                target.write_bytes(response.content)
                downloaded += 1
            except Exception as exc:  # una imagen rota no debe frenar el resto
                failed += 1
                print(f"  FALLO {url}: {exc}")

    print(
        f"Cache de imagenes: {downloaded} descargadas, "
        f"{skipped} ya existian, {failed} fallidas ({cache_dir})"
    )


if __name__ == "__main__":
    main()
