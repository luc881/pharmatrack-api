"""Carga guías de cuidados (Sitio → Fichas) desde un archivo JSON, por el API.

Uso (desde la carpeta pharmatrack-api):

    poetry run python scripts/import_care_sheets.py fichas.json --email tu@correo.com
    poetry run python scripts/import_care_sheets.py fichas.json --email tu@correo.com --aplicar

Sin --aplicar solo revisa y dice qué haría: cuáles crea, cuáles reemplaza y
qué tiene errores. No escribe nada. La contraseña la pide en la terminal (no
se escribe en el comando ni se guarda). Por omisión va a producción
(https://api.opuntiaden.com); --api http://localhost:8000 para la local.

- Cada ficha dice de qué especie es con "especie": el nombre científico
  ("Phyllium gardabagusi", con o sin localidad) o "species_id". Nunca crea
  especies: si no la encuentra, lo reporta.
- Si la especie ya tiene ficha, la reemplaza completa pero conserva su
  dirección (slug) y si está publicada. Las nuevas nacen SIN publicar: se
  revisan en el dashboard y se publican desde ahí.
- El resto de los campos son los del editor de fichas (ver
  scripts/fichas-ejemplo.json): summary (obligatorio), authority, origin,
  difficulty (Fácil, Intermedia, Difícil), taxonomy, facts, basics, body
  (Markdown; cada "## " es una sección), morphology, habitat, tags, photos,
  video, references.
"""
import argparse
import getpass
import json
import sys
import time
import unicodedata
from pathlib import Path

from pydantic import ValidationError

from pharmatrack.models.care_sheets.schemas import CareSheetCreate

API = "/api/v1"


def _plain(text) -> str:
    text = unicodedata.normalize("NFD", str(text or "").lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    for mark in "\"'“”‘’«»":
        text = text.replace(mark, " ")
    return " ".join(text.split())


def _scientific(species) -> str:
    return _plain(f"{(species.get('genus') or {}).get('name', '')} {species.get('name', '')}")


def _errors(exc: ValidationError) -> list[str]:
    return [
        f"{'.'.join(str(p) for p in e['loc']) or 'ficha'}: {e['msg'].removeprefix('Value error, ')}"
        for e in exc.errors()
    ]


def _get(client, headers, url):
    res = client.get(url, headers=headers)
    res.raise_for_status()
    return res.json()


def plan(client, headers, entries) -> list[dict]:
    """Qué haría con cada ficha, sin escribir nada."""
    species = _get(client, headers, f"{API}/species?page=1&page_size=500")
    species = species.get("data", species) if isinstance(species, dict) else species
    sheets = {s["species_id"]: s for s in _get(client, headers, f"{API}/care-sheets")}
    by_name = {}
    for sp in species:
        by_name.setdefault(_scientific(sp), sp)

    seen = set()
    result = []
    for index, raw in enumerate(entries, start=1):
        entry = dict(raw)
        wanted = entry.pop("especie", None)
        species_id = entry.pop("species_id", None)
        label = wanted or f"species_id {species_id}"
        item = {"n": index, "especie": label, "errors": []}

        sp = next((s for s in species if s["id"] == species_id), None) if species_id \
            else by_name.get(_plain(wanted))
        if not sp:
            item.update(action="error", errors=[f"La especie «{label}» no existe en el sistema."])
            result.append(item)
            continue
        item["especie"] = f"{sp['genus']['name']} {sp['name']}" if sp.get("genus") else label
        if sp["id"] in seen:
            item.update(action="error", errors=["Especie repetida en el archivo."])
            result.append(item)
            continue
        seen.add(sp["id"])

        existing = sheets.get(sp["id"])
        try:
            payload = CareSheetCreate.model_validate({
                **entry,
                "species_id": sp["id"],
                # al reemplazar se conserva la dirección y si está publicada
                **({"slug": existing["slug"], "published": existing["published"]} if existing
                   else {"published": False}),
            })
        except ValidationError as exc:
            item.update(action="error", errors=_errors(exc))
            result.append(item)
            continue

        body = payload.model_dump(mode="json", exclude_none=False)
        if existing:
            item.update(action="update", sheet_id=existing["id"], payload=body)
        else:
            body.pop("slug", None) if body.get("slug") is None else None
            item.update(action="create", payload=body)
        result.append(item)
    return result


def _send(client, method, url, headers, body):
    # producción limita las escrituras por minuto: se espera y se reintenta
    for _ in range(5):
        res = getattr(client, method)(url, json=body, headers=headers)
        if res.status_code != 429:
            return res
        time.sleep(float(res.headers.get("retry-after", 5)))
    return res


def apply(client, headers, planned) -> list[dict]:
    results = []
    for item in planned:
        if item["action"] == "error":
            results.append({"n": item["n"], "status": "skipped"})
            continue
        if item["action"] == "create":
            res = _send(client, "post", f"{API}/care-sheets", headers, item["payload"])
        else:
            res = _send(client, "put", f"{API}/care-sheets/{item['sheet_id']}", headers, item["payload"])
        ok = res.status_code in (200, 201)
        results.append({"n": item["n"], "status": "ok" if ok else "failed",
                        "detail": None if ok else res.text[:300]})
    return results


def main() -> None:
    import httpx

    parser = argparse.ArgumentParser(description="Carga guías de cuidados desde un JSON.")
    parser.add_argument("archivo", type=Path)
    parser.add_argument("--email", required=True)
    parser.add_argument("--api", default="https://api.opuntiaden.com")
    parser.add_argument("--aplicar", action="store_true", help="escribe de verdad (si no, solo revisa)")
    args = parser.parse_args()

    entries = json.loads(args.archivo.read_text(encoding="utf-8"))
    if isinstance(entries, dict):
        entries = [entries]

    with httpx.Client(base_url=args.api, timeout=30) as client:
        res = client.post(f"{API}/auth/token",
                          data={"username": args.email, "password": getpass.getpass("Contraseña: ")})
        if res.status_code != 200:
            sys.exit(f"No se pudo iniciar sesión ({res.status_code}).")
        headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

        planned = plan(client, headers, entries)
        names = {"create": "crear", "update": "reemplazar", "error": "ERROR"}
        for item in planned:
            print(f"{item['n']:>3}. {names[item['action']]:<10} {item['especie']}")
            for error in item["errors"]:
                print(f"       - {error}")
        counts = {k: sum(1 for p in planned if p["action"] == k) for k in names}
        print(f"\nCrear: {counts['create']} · Reemplazar: {counts['update']} · Con error: {counts['error']}")

        if not args.aplicar:
            print("\nSolo revisión. Para escribir, repite el comando con --aplicar.")
            return
        results = apply(client, headers, planned)
        failed = [r for r in results if r["status"] == "failed"]
        for r in failed:
            print(f"Falló la ficha {r['n']}: {r['detail']}")
        print(f"\nListo: {sum(r['status'] == 'ok' for r in results)} guardadas, {len(failed)} fallaron.")
        if counts["create"]:
            print("Las nuevas quedaron SIN publicar: revísalas y publícalas en Sitio → Fichas.")


if __name__ == "__main__":
    main()
