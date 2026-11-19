"""Da de alta animales (y productos) de otro expositor desde un JSON, por el API.

Uso (desde la carpeta pharmatrack-api):

    poetry run python scripts/import_animals.py scripts/bd-exoticos.json --email tu@correo.com
    poetry run python scripts/import_animals.py scripts/bd-exoticos.json --email tu@correo.com --aplicar

Sin --aplicar solo revisa y dice qué haría; no escribe nada. La contraseña la
pide en la terminal. Por omisión va a producción (https://api.opuntiaden.com);
--api http://localhost:8000 para la local.

El archivo (ver scripts/bd-exoticos.json):

- "proveedor": nombre del proveedor dueño, tal como está en Proveedores.
- "venta_rapida" / "en_el_sitio": cómo nacen los animales (por omisión
  venta rápida sí, sitio no).
- "especies_nuevas": las que no existan todavía, con su "grupo" (debe
  existir), "nombre_comun" y opcional "modo" (named / genes).
- "animales": uno por ejemplar, con "codigo" (si ya existe, se salta: se
  puede correr otra vez sin duplicar), "especie" (nombre científico),
  "sexo" (macho / hembra / sin sexar), "precio", "variedad" (lista de
  genes o variedades; las que no existan se crean) y "descripcion".
  Sin precio no se da de alta (se reporta).
- "productos": "nombre", "precio", "categoria" (se crea si no existe) y
  "se_prepara" (talón de orden en la venta rápida). Si ya hay uno con el
  mismo nombre, se salta.

- "especies": fichas de especie (Animales → Editar especie) y sus
  variedades, sin animales. Cada una: "especie" (nombre científico),
  "tambien_como" (otros nombres con que pudo darse de alta, para no
  duplicar), "grupo" (si hay que crearla), "campos" (common_name,
  description, origin, temperature, humidity, adult_size, difficulty,
  rarity, habitat, diet, notes) y "variedades" ([{"nombre", "tambien_como",
  "descripcion"}]). Si ya existe, solo llena lo vacío: lo que ya tiene otro
  valor se reporta y no se toca (la ficha de Animales manda), salvo los
  campos que diga "reemplazar". Los nombres de variedad van entre comillas
  simples ('Yellow'); al buscar se ignoran.

Una especie con «variedades con nombre» que reciba un ejemplar con varios
genes se cambia a «genes» (se avisa en la revisión).
"""
import argparse
import getpass
import itertools
import json
import sys
import time
import unicodedata
from pathlib import Path

API = "/api/v1"
SEXES = {"macho": "male", "hembra": "female", "sin sexar": "unknown"}


def _plain(text) -> str:
    text = unicodedata.normalize("NFD", str(text or "").lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    for mark in "\"'“”‘’«»":
        text = text.replace(mark, " ")
    return " ".join(text.split())


def _send(client, method, url, headers, body=None):
    # producción limita las peticiones por minuto: se espera y se reintenta
    for _ in range(5):
        kwargs = {"headers": headers}
        if body is not None:
            kwargs["json"] = body
        res = getattr(client, method)(url, **kwargs)
        if res.status_code != 429:
            return res
        time.sleep(float(res.headers.get("retry-after", 5)))
    return res


def _all(client, headers, url):
    """Todas las páginas de un listado paginado (o la lista tal cual)."""
    out = []
    for page in itertools.count(1):
        sep = "&" if "?" in url else "?"
        res = _send(client, "get", f"{url}{sep}page={page}&page_size=500", headers)
        res.raise_for_status()
        body = res.json()
        if isinstance(body, list):
            return body
        out += body["data"]
        if page >= body.get("total_pages", 1):
            return out


class Importer:
    """Revisa (y con apply=True escribe) en orden: lo creado antes da el id a lo
    que sigue. En revisión, lo que se crearía lleva un id negativo."""

    def __init__(self, client, headers, data, apply=False, log=print):
        self.client, self.headers, self.data, self.apply, self.log = client, headers, data, apply, log
        self.fake_ids = itertools.count(-1, -1)
        self.counts = {"creados": 0, "actualizados": 0, "ya estaban": 0, "con error": 0}

    def _create(self, url, body, what):
        if not self.apply:
            self.log(f"  crear {what}")
            return {**body, "id": next(self.fake_ids)}
        res = _send(self.client, "post", url, self.headers, body)
        if res.status_code not in (200, 201):
            raise RuntimeError(f"No se pudo crear {what}: {res.status_code} {res.text[:300]}")
        self.log(f"  creado {what}")
        return res.json()

    def _error(self, label, message):
        self.counts["con error"] += 1
        self.log(f"  ERROR {label}: {message}")

    # -- taxonomía -------------------------------------------------------

    def _species(self, scientific, new=None, aliases=(), fields=None):
        for name in (scientific, *aliases):
            if _plain(name) in self.species:
                return self.species[_plain(name)]
        key = _plain(scientific)
        new = new or {_plain(k): v for k, v in (self.data.get("especies_nuevas") or {}).items()}.get(key)
        if not new:
            raise LookupError(f"La especie «{scientific}» no existe; agrégala en «especies_nuevas».")
        genus_name, _, species_name = scientific.strip().partition(" ")
        # en Animales la especie va con mayúscula: «Arcangelii», «Sp.»
        species_name = species_name[:1].upper() + species_name[1:]
        genus = self.genera.get(_plain(genus_name))
        if not genus:
            group = self.groups.get(_plain(new["grupo"]))
            if not group:
                raise LookupError(f"El grupo «{new['grupo']}» no existe.")
            genus = self._create(f"{API}/genera", {"name": genus_name, "group_id": group["id"]},
                                 f"género {genus_name}")
            self.genera[_plain(genus_name)] = genus
        species = self._create(f"{API}/species", {
            "genus_id": genus["id"], "name": species_name, "common_name": new.get("nombre_comun"),
            "variety_mode": new.get("modo", "named"), **(fields or {}),
        }, f"especie {scientific}")
        species["_new"] = True
        self.species[key] = species
        return species

    def _fill(self, url, current, wanted, replace, label):
        """PUT solo de lo vacío (o de lo que diga replace); lo distinto se reporta."""
        patch = {}
        for field, value in wanted.items():
            now = current.get(field)
            if now in (None, "", []) or (field in replace and now != value):
                patch[field] = value
            elif now != value:
                self.log(f"  {label}: «{field}» ya tiene otro valor, no se cambia")
        if not patch:
            return
        if self.apply and current["id"] > 0:
            res = _send(self.client, "put", url, self.headers, patch)
            if res.status_code != 200:
                raise RuntimeError(f"No se pudo actualizar {label}: {res.status_code} {res.text[:300]}")
            self.log(f"  actualizado {label}: {', '.join(patch)}")
        else:
            self.log(f"  llenar {label}: {', '.join(patch)}")
        self.counts["actualizados"] += 1

    def _sheet(self, entry):
        label = entry["especie"]
        self.log(label)
        try:
            fields = entry.get("campos") or {}
            replace = set(entry.get("reemplazar") or [])
            species = self._species(entry["especie"], new={"grupo": entry.get("grupo")} if entry.get("grupo") else None,
                                    aliases=entry.get("tambien_como") or (), fields=fields)
            if species.pop("_new", False):
                self.counts["creados"] += 1
            else:
                self.log(f"  ya existe (#{species['id']})")
                self._fill(f"{API}/species/{species['id']}", species, fields, replace, "especie")
            known = self.morphs.setdefault(species["id"], {})
            for variety in entry.get("variedades") or []:
                names = [variety["nombre"], *(variety.get("tambien_como") or [])]
                morph = next((known[_plain(n)] for n in names if _plain(n) in known), None)
                wanted = {"description": variety["descripcion"]} if variety.get("descripcion") else {}
                if morph:
                    self.log(f"  variedad {morph['name']} ya existe (#{morph['id']})")
                    self._fill(f"{API}/morphs/{morph['id']}", morph, wanted, replace, f"variedad {morph['name']}")
                else:
                    known[_plain(variety["nombre"])] = self._create(
                        f"{API}/morphs", {"species_id": species["id"], "name": variety["nombre"], **wanted},
                        f"variedad {variety['nombre']}")
                    self.counts["creados"] += 1
        except (LookupError, RuntimeError) as exc:
            self._error(label, str(exc))

    def _morph_ids(self, species, names):
        if len(names) > 1 and species.get("variety_mode", "named") == "named":
            label = f"{species.get('common_name') or species['name']} a «genes» (combina varios)"
            if self.apply and species["id"] > 0:
                res = _send(self.client, "put", f"{API}/species/{species['id']}", self.headers,
                            {"variety_mode": "genes"})
                if res.status_code != 200:
                    raise RuntimeError(f"No se pudo cambiar {label}: {res.text[:300]}")
                self.log(f"  cambiada {label}")
            else:
                self.log(f"  cambiar {label}")
            species["variety_mode"] = "genes"
        ids = []
        for name in names:
            known = self.morphs.setdefault(species["id"], {})
            morph = known.get(_plain(name))
            if not morph:
                morph = self._create(f"{API}/morphs", {"species_id": species["id"], "name": name},
                                     f"variedad {name}")
                known[_plain(name)] = morph
            ids.append(morph["id"])
        return ids

    # -- todo ------------------------------------------------------------

    def run(self):
        c, h = self.client, self.headers
        self.groups = {_plain(g["name"]): g for g in _all(c, h, f"{API}/animal-groups")}
        self.genera = {_plain(g["name"]): g for g in _all(c, h, f"{API}/genera")}
        self.species = {
            _plain(f"{s['genus']['name']} {s['name']}"): s for s in _all(c, h, f"{API}/species") if s.get("genus")
        }
        self.morphs = {}
        for m in _all(c, h, f"{API}/morphs"):
            self.morphs.setdefault(m["species_id"], {})[_plain(m["name"])] = m

        for entry in self.data.get("especies") or []:
            self._sheet(entry)
        if not (self.data.get("animales") or self.data.get("productos")):
            return self.counts

        suppliers = _all(c, h, f"{API}/suppliers")
        supplier = next((s for s in suppliers if _plain(s["name"]) == _plain(self.data.get("proveedor"))), None)
        if not supplier:
            self._error("proveedor", f"«{self.data.get('proveedor')}» no existe en Proveedores.")
            return self.counts
        codes = {_plain(a["code"]) for a in _all(c, h, f"{API}/animals")}

        quick = self.data.get("venta_rapida", True)
        on_site = self.data.get("en_el_sitio", False)
        for entry in self.data.get("animales", []):
            label = f"{entry.get('codigo')} {entry.get('especie')} {' '.join(entry.get('variedad') or [])}".strip()
            self.log(label)
            if _plain(entry.get("codigo")) in codes:
                self.counts["ya estaban"] += 1
                self.log("  ya existe, se salta")
                continue
            if entry.get("precio") is None:
                self._error(label, "falta el precio")
                continue
            if entry.get("sexo") not in SEXES:
                self._error(label, f"sexo «{entry.get('sexo')}»: usa macho, hembra o sin sexar")
                continue
            try:
                species = self._species(entry["especie"])
                morph_ids = self._morph_ids(species, entry.get("variedad") or [])
                self._create(f"{API}/animals", {
                    "species_id": species["id"], "code": entry["codigo"], "sex": SEXES[entry["sexo"]],
                    "price": entry["precio"], "morph_ids": morph_ids,
                    "description": entry.get("descripcion"), "consignor_id": supplier["id"],
                    "quick_sale": quick, "show_public": on_site,
                }, f"ejemplar {entry['codigo']} (${entry['precio']:,})")
                self.counts["creados"] += 1
            except (LookupError, RuntimeError) as exc:
                self._error(label, str(exc))

        products = self.data.get("productos") or []
        if products:
            categories = {_plain(x["name"]): x for x in _all(c, h, f"{API}/productscategories")}
        for item in products:
            self.log(item["nombre"])
            found = _all(c, h, f"{API}/products?search={item['nombre']}")
            if any(_plain(p["title"]) == _plain(item["nombre"]) for p in found):
                self.counts["ya estaban"] += 1
                self.log("  ya existe, se salta")
                continue
            try:
                category = categories.get(_plain(item["categoria"]))
                if not category:
                    category = self._create(f"{API}/productscategories", {"name": item["categoria"]},
                                            f"categoría {item['categoria']}")
                    categories[_plain(item["categoria"])] = category
                self._create(f"{API}/products", {
                    "title": item["nombre"], "price_retail": item["precio"], "price_cost": 0,
                    "product_category_id": category["id"], "tracks_batches": False,
                    "quick_sale": True, "needs_prep": item.get("se_prepara", False),
                    "consignor_id": supplier["id"],
                }, f"producto ${item['precio']:,}")
                self.counts["creados"] += 1
            except RuntimeError as exc:
                self._error(item["nombre"], str(exc))
        return self.counts


def main() -> None:
    import httpx

    parser = argparse.ArgumentParser(description="Alta de animales y productos de otro expositor.")
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
        counts = Importer(client, headers, data, apply=args.aplicar).run()

    verb = "Creados" if args.aplicar else "Por crear"
    print(f"\n{verb}: {counts['creados']} · Llenados: {counts['actualizados']} · "
          f"Ya estaban: {counts['ya estaban']} · Con error: {counts['con error']}")
    if not args.aplicar:
        print("Solo revisión. Para escribir, repite el comando con --aplicar.")


if __name__ == "__main__":
    main()
