"""Corrige animales ya dados de alta con import_animals.py para que queden como
dice su JSON (el mismo archivo, ya corregido).

Uso (desde la carpeta pharmatrack-api):

    poetry run python scripts/corregir_variedades.py scripts/bd-exoticos.json --email tu@correo.com
    poetry run python scripts/corregir_variedades.py scripts/bd-exoticos.json --email tu@correo.com --aplicar

Sin --aplicar solo dice qué haría. Con --aplicar:

1. A cada animal del archivo (por código) le deja las variedades y la
   descripción del archivo.
2. Las variedades del archivo que estén guardadas sin comillas se renombran
   con comillas simples (Pied → 'Pied').
3. Borra las variedades «Het …» de esas especies que ya no tenga ningún
   animal (los het van en la descripción, no como variedad). El API no deja
   borrar una variedad que algún animal todavía use.
"""
import argparse
import getpass
import importlib.util
import json
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("import_animals", Path(__file__).with_name("import_animals.py"))
_ia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ia)
API, _all, _plain, _send = _ia.API, _ia._all, _ia._plain, _ia._send


def run(client, headers, data, apply=False, log=print) -> dict:
    counts = {"cambios": 0, "con error": 0}

    def do(method, url, body, label):
        counts["cambios"] += 1
        if not apply:
            log(f"  {label}")
            return
        res = _send(client, method, url, headers, body)
        if res.status_code not in (200, 204):
            counts["con error"] += 1
            log(f"  ERROR {label}: {res.status_code} {res.text[:300]}")
        else:
            log(f"  hecho: {label}")

    animals = {_plain(a["code"]): a for a in _all(client, headers, f"{API}/animals")}
    morphs = {}
    for m in _all(client, headers, f"{API}/morphs"):
        morphs.setdefault(m["species_id"], []).append(m)

    wanted_names = {}  # (species_id, nombre plano) → nombre con comillas del archivo
    after = {}  # código → variedades que tendrá
    touched = set()  # especies del archivo
    for entry in data.get("animales", []):
        animal = animals.get(_plain(entry["codigo"]))
        if not animal:
            log(f"{entry['codigo']}: no está dado de alta, se salta")
            continue
        sid = animal["species_id"]
        touched.add(sid)
        by_name = {_plain(m["name"]): m for m in morphs.get(sid, [])}
        ids, missing = [], []
        for name in entry.get("variedad") or []:
            wanted_names[(sid, _plain(name))] = name
            (ids.append(by_name[_plain(name)]["id"]) if _plain(name) in by_name else missing.append(name))
        log(entry["codigo"])
        if missing:
            counts["con error"] += 1
            log(f"  ERROR no existe la variedad {', '.join(missing)}; no se toca")
            continue
        after[_plain(entry["codigo"])] = ids
        patch = {}
        if sorted(m["id"] for m in animal.get("morphs", [])) != sorted(ids):
            patch["morph_ids"] = ids
        if (animal.get("description") or None) != (entry.get("descripcion") or None):
            patch["description"] = entry.get("descripcion")
        if patch:
            names = [m["name"] for m in morphs[sid] if m["id"] in ids] if "morph_ids" in patch else None
            what = []
            if names is not None:
                what.append(f"variedades → {', '.join(names) or 'nominal'}")
            if "description" in patch:
                what.append(f"descripción → «{patch['description'] or ''}»")
            do("put", f"{API}/animals/{animal['id']}", patch, "; ".join(what))

    log("Variedades")
    for (sid, plain), name in sorted(wanted_names.items()):
        morph = next((m for m in morphs.get(sid, []) if _plain(m["name"]) == plain), None)
        if morph and morph["name"] != name:
            do("put", f"{API}/morphs/{morph['id']}", {"name": name}, f"renombrar {morph['name']} → {name}")

    # het sueltos de las especies del archivo: solo los que nadie usará tras el paso 1
    in_use = set()
    for code, a in animals.items():
        in_use |= set(after.get(code, [m["id"] for m in a.get("morphs", [])]))
    for sid in sorted(touched):
        for m in morphs.get(sid, []):
            if _plain(m["name"]).startswith("het ") and m["id"] not in in_use:
                do("delete", f"{API}/morphs/{m['id']}", None, f"borrar variedad {m['name']}")
    return counts


def main() -> None:
    import httpx

    parser = argparse.ArgumentParser(description="Corrige variedades y descripciones de animales ya dados de alta.")
    parser.add_argument("archivo", type=Path)
    parser.add_argument("--email", required=True)
    parser.add_argument("--api", default="https://api.opuntiaden.com")
    parser.add_argument("--aplicar", action="store_true", help="escribe de verdad (si no, solo revisa)")
    args = parser.parse_args()

    data = json.loads(args.archivo.read_text(encoding="utf-8"))
    with httpx.Client(base_url=args.api, timeout=30) as client:
        res = client.post(f"{API}/auth/token",
                          data={"username": args.email, "password": getpass.getpass("Contraseña: ")})
        if res.status_code != 200:
            sys.exit(f"No se pudo iniciar sesión ({res.status_code}).")
        headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
        counts = run(client, headers, data, apply=args.aplicar)

    verb = "Hechos" if args.aplicar else "Por hacer"
    print(f"\n{verb}: {counts['cambios']} cambios · Con error: {counts['con error']}")
    if not args.aplicar:
        print("Solo revisión. Para escribir, repite el comando con --aplicar.")


if __name__ == "__main__":
    main()
