import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette import status

from ...db.session import db_dependency
from ...models.app_settings.orm import AppSetting
from ...utils.permissions import CAN_READ_SALES, CAN_UPDATE_SALES, CAN_UPDATE_ANIMAL_GROUPS

router = APIRouter(prefix="/settings", tags=["settings"])

# Defaults de la plantilla del correo de ticket; lo guardado los sobreescribe
EMAIL_TICKET_DEFAULTS = {
    "business_name": "Opuntia Den",
    "intro_message": "",
    "footer_message": "Gracias por su compra.",
}


def get_email_ticket_template(db) -> dict:
    row = db.query(AppSetting).filter(AppSetting.key == "email_ticket").first()
    stored = json.loads(row.value) if row else {}
    return {**EMAIL_TICKET_DEFAULTS, **stored}


class EmailTicketTemplate(BaseModel):
    business_name: str = EMAIL_TICKET_DEFAULTS["business_name"]
    intro_message: str = ""
    footer_message: str = EMAIL_TICKET_DEFAULTS["footer_message"]


@router.get("/email-ticket", dependencies=CAN_READ_SALES,
            summary="Plantilla del correo de ticket")
def read_email_ticket(db: db_dependency):
    return get_email_ticket_template(db)


@router.put("/email-ticket", dependencies=CAN_UPDATE_SALES,
            summary="Guardar plantilla del correo de ticket")
def update_email_ticket(body: EmailTicketTemplate, db: db_dependency):
    if not body.business_name.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="El nombre del negocio no puede quedar vacio.")
    row = db.query(AppSetting).filter(AppSetting.key == "email_ticket").first()
    if not row:
        row = AppSetting(key="email_ticket", value="{}")
        db.add(row)
    row.value = json.dumps(body.model_dump())
    db.commit()
    return get_email_ticket_template(db)


# =========================================================
# Ajustes del sitio publico
# =========================================================
SITE_DEFAULTS = {
    "show_category_browse": True,  # seccion "Explora por grupo" en la home
}


def get_site_settings(db) -> dict:
    row = db.query(AppSetting).filter(AppSetting.key == "site").first()
    stored = json.loads(row.value) if row else {}
    return {**SITE_DEFAULTS, **stored}


class SiteSettings(BaseModel):
    show_category_browse: bool = True


# Lectura publica (sin auth): el sitio la consulta para armar la home
@router.get("/site", summary="Ajustes publicos del sitio")
def read_site_settings(db: db_dependency):
    return get_site_settings(db)


@router.put("/site", dependencies=CAN_UPDATE_ANIMAL_GROUPS,
            summary="Guardar ajustes del sitio")
def update_site_settings(body: SiteSettings, db: db_dependency):
    row = db.query(AppSetting).filter(AppSetting.key == "site").first()
    if not row:
        row = AppSetting(key="site", value="{}")
        db.add(row)
    row.value = json.dumps(body.model_dump())
    db.commit()
    return get_site_settings(db)
