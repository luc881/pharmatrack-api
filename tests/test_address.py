"""Direccion estructurada del cliente y utilidades de CP."""
from .utils import client
from .test_shop import fake_google, _sign_in  # noqa: F401
from pharmatrack.utils.mx_address import state_for_zip, format_address


def test_state_for_zip():
    assert state_for_zip("06700") == "Ciudad de México"
    assert state_for_zip("44100") == "Jalisco"
    assert state_for_zip("64000") == "Nuevo León"
    # fuera de rango o mal formado: no adivina
    assert state_for_zip("00100") is None
    assert state_for_zip("123") is None
    assert state_for_zip("abcde") is None
    assert state_for_zip("") is None


def test_format_address_skips_missing_parts():
    assert format_address({"street": "Av. Reforma", "ext_number": "222",
                           "neighborhood": "Juárez", "zip_code": "06600",
                           "city": "Cuauhtémoc", "state": "Ciudad de México"}) == (
        "Av. Reforma 222\nJuárez\nCP 06600, Cuauhtémoc, Ciudad de México"
    )
    # solo lo que hay, sin comas ni renglones sueltos
    assert format_address({"street": "Calle 5"}) == "Calle 5"
    assert format_address({}) == ""


def test_address_roundtrip_and_derived_text(fake_google):  # noqa: F811
    headers = _sign_in()
    res = client.put("/api/v1/shop/me", headers=headers, json={
        "street": "Av. Reforma", "ext_number": "222", "int_number": "4B",
        "neighborhood": "Juárez", "zip_code": "06600", "city": "Cuauhtémoc",
        "state": "Ciudad de México", "address_notes": "Portón negro",
    })
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["zip_code"] == "06600"
    # el texto derivado se arma solo: es lo que copian pedidos y correos
    assert "Av. Reforma 222 Int. 4B" in body["address"]
    assert "Referencias: Portón negro" in body["address"]

    # cambiar una sola parte recompone el texto sin borrar el resto
    res = client.put("/api/v1/shop/me", headers=headers, json={"ext_number": "300"})
    assert res.status_code == 200
    assert "Av. Reforma 300" in res.json()["address"]
    assert res.json()["neighborhood"] == "Juárez"


def test_bad_zip_is_rejected(fake_google):  # noqa: F811
    headers = _sign_in()
    for bad in ("123", "abcde", "0660O"):
        res = client.put("/api/v1/shop/me", headers=headers, json={"zip_code": bad})
        assert res.status_code == 422, bad


def test_mx_states_is_public():
    res = client.get("/api/v1/shop/mx-states")
    assert res.status_code == 200
    states = res.json()
    assert len(states) == 32
    assert "Ciudad de México" in states
