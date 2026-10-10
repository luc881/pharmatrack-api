"""Contenido de /gracias y /links: lectura publica, guardado validado."""
import copy

from pharmatrack.api.routes.settings import LINK_PAGES_DEFAULTS
from .utils import client

URL = "/api/v1/settings/link-pages"


def test_lectura_publica_trae_los_defaults():
    data = client.get(URL).json()
    assert data["events"][0]["date"] == "2026-11-21"
    assert set(data["pages"]) == {"gracias", "links"}


def test_guardar_y_leer(auth_headers):
    body = copy.deepcopy(LINK_PAGES_DEFAULTS)
    body["pages"]["links"]["title"] = "Otro titular"
    body["events"] = []
    res = client.put(URL, json=body, headers=auth_headers)
    assert res.status_code == 200, res.text
    data = client.get(URL).json()
    assert data["pages"]["links"]["title"] == "Otro titular"
    assert data["events"] == []


def test_rechaza_urls_peligrosas(auth_headers):
    for bad in ("javascript:alert(1)", "//evil.com", "data:text/html,x"):
        body = copy.deepcopy(LINK_PAGES_DEFAULTS)
        body["pages"]["gracias"]["buttons"][0]["url"] = bad
        assert client.put(URL, json=body, headers=auth_headers).status_code == 422, bad


def test_sin_sesion_no_guarda():
    assert client.put(URL, json=LINK_PAGES_DEFAULTS).status_code == 401
