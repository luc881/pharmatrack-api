"""Rollo y ajuste de la impresora de tickets: se guardan por usuario."""
from .utils import client


def test_sin_guardar_trae_defaults(auth_headers):
    res = client.get("/api/v1/settings/ticket-print", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == {"width": 80, "offset": 0, "saved": False}


def test_guarda_y_lee_lo_del_usuario(auth_headers):
    res = client.put("/api/v1/settings/ticket-print",
                     json={"width": 58, "offset": -1.3000001}, headers=auth_headers)
    assert res.status_code == 200
    got = client.get("/api/v1/settings/ticket-print", headers=auth_headers).json()
    assert got == {"width": 58, "offset": -1.3, "saved": True}


def test_rechaza_rollo_o_ajuste_fuera_de_rango(auth_headers):
    for body in ({"width": 70, "offset": 0}, {"width": 58, "offset": 9}):
        res = client.put("/api/v1/settings/ticket-print", json=body, headers=auth_headers)
        assert res.status_code == 422


def test_requiere_sesion():
    assert client.get("/api/v1/settings/ticket-print").status_code == 401
