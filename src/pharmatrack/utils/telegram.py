"""Recordatorio diario del plan de manejo por Telegram.

Corre dentro del API (lifespan): cada 10 min revisa si ya pasó la hora del
recordatorio; el primer worker que "aparta" el día en app_settings lo manda,
así con varios workers sale uno solo.
"""
import asyncio
from datetime import date, datetime, timedelta

import httpx
from sqlalchemy import text

from pharmatrack.config import settings
from pharmatrack.utils.logger import get_logger

logger = get_logger(__name__)

SENT_KEY = "telegram_reminder_sent"
HOUR_KEY = "telegram_reminder_hour"  # hora de CDMX, se elige en la bitácora
DEFAULT_HOUR = 8
MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def configured() -> bool:
    return bool(settings.telegram_bot_token and settings.telegram_chat_id)


def send(message: str) -> None:
    """Errores sin la URL: lleva el token."""
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    for chat_id in settings.telegram_chat_id.split(","):
        try:
            res = httpx.post(url, json={"chat_id": chat_id.strip(), "text": message}, timeout=15)
        except httpx.HTTPError:
            raise RuntimeError("sin conexión con Telegram") from None
        if not res.is_success:
            raise RuntimeError(res.json().get("description", f"HTTP {res.status_code}"))


def _due(days_overdue: int) -> str:
    if days_overdue == 0:
        return "toca hoy"
    return f"atrasado {days_overdue} día{'s' if days_overdue > 1 else ''}"


def reminder_text(rows: list[dict], today: date) -> str:
    """Lo que ya toca o está atrasado, por especie. Vacío si todo está al día."""
    blocks = []
    for r in rows:
        items = [p for p in r["plan"] if p["days_overdue"] >= 0]
        if not items:
            continue
        lines = [r["common_name"] or r["species_name"]]
        for p in items:
            who = f" ({', '.join(p['pending_codes'])})" if p.get("pending_codes") else ""
            lines.append(f"• {p['name']} — {_due(p['days_overdue'])}{who}")
        blocks.append("\n".join(lines))
    if not blocks:
        return ""
    return f"🦎 Pendientes del plan · {today.day} {MONTHS[today.month - 1]}\n\n" + "\n\n".join(blocks)


def get_hour(db) -> int:
    row = db.execute(text("SELECT value FROM app_settings WHERE key = :k"), {"k": HOUR_KEY}).first()
    return int(row.value) if row else DEFAULT_HOUR


def set_hour(db, hour: int) -> None:
    db.execute(text(
        "INSERT INTO app_settings (key, value) VALUES (:k, :v) "
        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
    ), {"k": HOUR_KEY, "v": str(hour)})
    db.commit()


def _claim(db, value: str) -> bool:
    row = db.execute(text(
        "INSERT INTO app_settings (key, value) VALUES (:k, :v) "
        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value "
        "WHERE app_settings.value < EXCLUDED.value RETURNING key"
    ), {"k": SENT_KEY, "v": value}).first()
    db.commit()
    return row is not None


def _tick() -> None:
    from pharmatrack.api.routes.husbandry_logs import CDMX, status_rows
    from pharmatrack.db.session import SessionLocal

    now = datetime.now(CDMX)
    db = SessionLocal()
    try:
        if now.hour < get_hour(db) or not _claim(db, now.date().isoformat()):
            return
        try:
            message = reminder_text(status_rows(db), now.date())
            if message:
                send(message)
        except Exception:
            # suelta el día para reintentar en la siguiente vuelta
            db.rollback()
            db.execute(text("UPDATE app_settings SET value = :v WHERE key = :k"),
                       {"k": SENT_KEY, "v": (now.date() - timedelta(days=1)).isoformat()})
            db.commit()
            raise
    finally:
        db.close()


async def reminder_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(_tick)
        except Exception:
            logger.exception("No salió el recordatorio de Telegram")
        await asyncio.sleep(600)
