import resend
from pharmatrack.config import settings
from pharmatrack.utils.logger import get_logger

logger = get_logger(__name__)

FROM_ADDRESS = "noreply@farmaciaselene.com"


def send_password_reset_email(to_email: str, token: str) -> None:
    reset_link = f"{settings.frontend_url}/auth/reset-password?token={token}"

    logger.info(
        "Sending password reset email to=%s frontend_url=%s api_key_set=%s",
        to_email,
        settings.frontend_url,
        bool(settings.resend_api_key),
    )

    client = resend.Resend(api_key=settings.resend_api_key)

    response = client.emails.send({
        "from": FROM_ADDRESS,
        "to": [to_email],
        "subject": "Restablecer contraseña — PharmaTrack",
        "html": f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="font-family: sans-serif; color: #1a1a1a; max-width: 480px; margin: 0 auto; padding: 24px;">
  <h2 style="color: #2563eb;">PharmaTrack</h2>
  <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta.</p>
  <p>Haz clic en el siguiente botón para continuar. El enlace es válido por <strong>15 minutos</strong>.</p>
  <a href="{reset_link}"
     style="display: inline-block; margin: 16px 0; padding: 12px 24px;
            background-color: #2563eb; color: #ffffff; text-decoration: none;
            border-radius: 6px; font-weight: 600;">
    Restablecer contraseña
  </a>
  <p style="color: #6b7280; font-size: 13px;">
    Si no solicitaste este cambio, ignora este correo. Tu contraseña no será modificada.
  </p>
  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
  <p style="color: #9ca3af; font-size: 12px;">
    Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
    <a href="{reset_link}" style="color: #2563eb;">{reset_link}</a>
  </p>
</body>
</html>
""",
    })

    logger.info("Password reset email sent to=%s resend_id=%s", to_email, response.id)
