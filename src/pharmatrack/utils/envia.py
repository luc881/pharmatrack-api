"""Envia.com: cotizar paqueterías y generar guías desde el dashboard.

Herramienta interna: el cliente nunca la toca. Quien atiende el pedido revisa
la dirección, mide el paquete, cotiza, elige paquetería y genera la guía.

ponytail: tres llamadas HTTP con httpx (paqueterías, cotizar, generar), sin
SDK. Sin webhooks de rastreo: el estado del pedido se sigue cambiando a mano;
agregarlos cuando el volumen de envíos lo pida.

Docs: https://docs.envia.com/docs/core-workflow
"""
import json
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import httpx
from fastapi import HTTPException
from starlette import status

from pharmatrack.config import settings
from pharmatrack.utils.logger import get_logger

logger = get_logger(__name__)

# Campos que Envia exige en el remitente (ENVIA_ORIGIN)
ORIGIN_REQUIRED = ("name", "phone", "street", "city", "state", "postalCode")


def is_configured() -> bool:
    return bool(settings.envia_api_token.strip() and settings.envia_origin.strip())


def _hosts() -> tuple[str, str]:
    """(envíos, consultas). El token de pruebas solo sirve en los hosts de
    pruebas y el productivo en los productivos."""
    if settings.envia_sandbox:
        return "https://api-test.envia.com", "https://queries.test.envia.com"
    return "https://api.envia.com", "https://queries.envia.com"


def _require_configured() -> None:
    if not is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Los envíos con Envia.com no están configurados (ENVIA_API_TOKEN y ENVIA_ORIGIN).",
        )


def _origin() -> dict:
    try:
        origin = json.loads(settings.envia_origin)
    except ValueError:
        origin = None
    if not isinstance(origin, dict) or any(not origin.get(k) for k in ORIGIN_REQUIRED):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ENVIA_ORIGIN debe ser un JSON con: " + ", ".join(ORIGIN_REQUIRED) + ".",
        )
    # el estado puede venir con nombre («Jalisco») o con el código de Envia («JA»)
    return {"country": "MX", **origin, "state": state_code(origin["state"])}


def _call(method: str, url: str, **kwargs) -> dict:
    headers = {"Authorization": f"Bearer {settings.envia_api_token.strip()}"}
    try:
        res = httpx.request(method, url, headers=headers, timeout=25, **kwargs)
    except httpx.HTTPError as exc:
        logger.error("Envia.com no responde (%s): %s", url, exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Envia.com no responde. Intenta de nuevo.")
    if res.status_code == 402:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED,
                            detail="La cuenta de Envia.com no tiene saldo para esta guía.")
    if res.status_code >= 400:
        logger.warning("Envia.com %s en %s: %s", res.status_code, url, res.text[:500])
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Envia.com rechazó la solicitud: {res.text[:300]}")
    try:
        return res.json()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Envia.com respondió algo que no se pudo leer.")


def _norm(text: str) -> str:
    """Sin acentos ni mayúsculas, para comparar nombres de estados."""
    plain = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return " ".join(plain.lower().split())


@lru_cache(maxsize=1)
def _state_codes() -> dict:
    """Nombre normalizado → código de 2 letras, de la lista de Envia."""
    data = _call("GET", f"{_hosts()[1]}/state", params={"country_code": "MX"}).get("data") or []
    return {_norm(s.get("name", "")): s.get("code_2_digits") for s in data if s.get("code_2_digits")}


def state_code(name: str) -> str:
    """Código de Envia para un estado escrito como en MX_STATES."""
    codes = _state_codes()
    wanted = _norm(name)
    # Envia puede llamar «México» o «Estado de México» al mismo estado
    for candidate in (wanted, wanted.replace("estado de ", ""), f"estado de {wanted}"):
        if candidate in codes:
            return codes[candidate]
    if len(name.strip()) == 2 and name.strip().upper() in codes.values():
        return name.strip().upper()
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Envia.com no reconoce el estado «{name}».")


@lru_cache(maxsize=1)
def carriers() -> tuple:
    """Paqueterías activas en México (su `name` es el identificador)."""
    data = _call("GET", f"{_hosts()[1]}/carrier", params={"country_code": "MX"}).get("data") or []
    return tuple(c["name"] for c in data if c.get("name") and c.get("active", True))


def _payload(destination: dict, package: dict, carrier: str, service: str | None = None) -> dict:
    dest = {
        "name": destination["name"],
        "phone": destination["phone"],
        "street": destination["street"],
        "number": destination.get("number") or "",
        "district": destination.get("district") or "",
        "city": destination["city"],
        "state": state_code(destination["state"]),
        "country": "MX",
        "postalCode": destination["postal_code"],
        "reference": destination.get("reference") or "",
    }
    shipment = {"type": 1, "carrier": carrier}
    if service:
        shipment["service"] = service
    return {
        "origin": _origin(),
        "destination": dest,
        "packages": [{
            "type": "box",
            "content": package["content"],
            "amount": 1,
            "declaredValue": float(package.get("declared_value") or 0),
            "lengthUnit": "CM",
            "weightUnit": "KG",
            "weight": float(package["weight"]),
            "dimensions": {
                "length": float(package["length"]),
                "width": float(package["width"]),
                "height": float(package["height"]),
            },
        }],
        "shipment": shipment,
        "settings": {"currency": "MXN", "printFormat": "PDF", "printSize": "STOCK_4X6"},
    }


def rates(destination: dict, package: dict) -> list[dict]:
    """Cotiza con todas las paqueterías (Envia acepta una por petición) y
    devuelve las opciones de la más barata a la más cara. Una paquetería que
    falla o no cubre la ruta simplemente no aparece."""
    _require_configured()
    url = f"{_hosts()[0]}/ship/rate/"
    # se arma una vez antes de los hilos: valida origen y estado, y si algo
    # está mal falla aquí con su mensaje en vez de perderse en cada hilo
    base = _payload(destination, package, "")

    def quote(carrier: str) -> list[dict]:
        try:
            body = {**base, "shipment": {"type": 1, "carrier": carrier}}
            return _call("POST", url, json=body).get("data") or []
        except HTTPException:
            return []

    names = carriers()
    with ThreadPoolExecutor(max_workers=8) as pool:
        found = [q for quotes in pool.map(quote, names) for q in quotes]

    options = []
    for q in found:
        try:
            price = float(q["totalPrice"])
        except (KeyError, TypeError, ValueError):
            continue
        options.append({
            "carrier": q.get("carrier"),
            "service": q.get("service"),
            "description": q.get("serviceDescription") or q.get("service"),
            "delivery_estimate": q.get("deliveryEstimate"),
            "price": price,
            "currency": q.get("currency") or "MXN",
        })
    return sorted(options, key=lambda o: o["price"])


def generate(destination: dict, package: dict, carrier: str, service: str) -> dict:
    """Genera (y cobra) la guía. Devuelve guía, rastreo, PDF y costo."""
    _require_configured()
    body = _payload(destination, package, carrier, service)
    data = _call("POST", f"{_hosts()[0]}/ship/generate/", json=body).get("data") or []
    if not data or not data[0].get("trackingNumber"):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Envia.com no devolvió una guía.")
    label = data[0]
    return {
        "carrier": label.get("carrier") or carrier,
        "service": label.get("service") or service,
        "tracking_number": str(label["trackingNumber"]),
        "tracking_url": label.get("trackUrl"),
        "label_url": label.get("label"),
        "cost": label.get("totalPrice"),
    }
