"""Verificación del id_token de Google (unidad, sin llamar a Google)."""
import pytest
from fastapi import HTTPException

from pharmatrack.utils import google_auth
from pharmatrack.utils.google_auth import verify_google_id_token

CLIENT_ID = "72648437073-abc.apps.googleusercontent.com"

GOOD = {
    "aud": CLIENT_ID,
    "iss": "https://accounts.google.com",
    "sub": "g-1",
    "email": "Persona@Example.com",
    "email_verified": "true",
    "name": "Persona",
    "picture": None,
}


class _Resp:
    status_code = 200

    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


def _setup(monkeypatch, configured_id, payload):
    monkeypatch.setattr(google_auth.settings, "google_client_id", configured_id)
    monkeypatch.setattr(google_auth.httpx, "get", lambda *a, **k: _Resp(payload))


def test_accepts_matching_aud_and_lowercases_email(monkeypatch):
    _setup(monkeypatch, CLIENT_ID, GOOD)
    assert verify_google_id_token("tok")["email"] == "persona@example.com"


def test_tolerates_pasted_whitespace_and_quotes(monkeypatch):
    # lo que pasa al pegar en el panel de variables: comillas o espacios
    _setup(monkeypatch, f'  "{CLIENT_ID}" \n', GOOD)
    assert verify_google_id_token("tok")["sub"] == "g-1"


def test_rejects_token_for_another_app(monkeypatch):
    _setup(monkeypatch, CLIENT_ID, {**GOOD, "aud": "otra-app.apps.googleusercontent.com"})
    with pytest.raises(HTTPException) as e:
        verify_google_id_token("tok")
    assert e.value.status_code == 401


def test_rejects_unverified_email(monkeypatch):
    _setup(monkeypatch, CLIENT_ID, {**GOOD, "email_verified": "false"})
    with pytest.raises(HTTPException) as e:
        verify_google_id_token("tok")
    assert e.value.status_code == 401


def test_503_when_not_configured(monkeypatch):
    _setup(monkeypatch, "", GOOD)
    with pytest.raises(HTTPException) as e:
        verify_google_id_token("tok")
    assert e.value.status_code == 503
