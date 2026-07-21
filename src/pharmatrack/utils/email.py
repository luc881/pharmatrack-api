import resend
from pharmatrack.config import settings
from pharmatrack.utils.logger import get_logger

logger = get_logger(__name__)

# Configurable via EMAIL_FROM (migracion de dominio sin tocar codigo)
FROM_ADDRESS = settings.email_from


def send_password_reset_email(to_email: str, token: str) -> None:
    reset_link = f"{settings.frontend_url}/auth/reset-password?token={token}"

    logger.info(
        "Sending password reset email to=%s frontend_url=%s api_key_set=%s",
        to_email,
        settings.frontend_url,
        bool(settings.resend_api_key),
    )

    resend.api_key = settings.resend_api_key

    response = resend.Emails.send({
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

    logger.info("Password reset email sent to=%s resend_id=%s", to_email, response.get("id"))


PAYMENT_LABELS = {"cash": "Efectivo", "card": "Tarjeta", "transfer": "Transferencia"}


def send_ticket_email(to_email: str, sale_id: int, date_str: str, items: list[dict],
                      payments: list[dict], total: float, change: float,
                      template: dict | None = None) -> None:
    """Ticket de venta por correo. items: [{title, quantity, unit_price, discount, subtotal}]."""
    rows = "".join(
        f"""<tr>
          <td style="padding:6px 8px;border-bottom:1px solid #e5e7eb;">{i['title']}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #e5e7eb;text-align:right;">{i['quantity']:g} x ${i['unit_price']:.2f}{f" (desc ${i['discount']:.2f})" if i['discount'] else ""}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #e5e7eb;text-align:right;">${i['subtotal']:.2f}</td>
        </tr>"""
        for i in items
    )
    pay_rows = "".join(
        f"""<tr><td style="padding:4px 8px;color:#6b7280;">{PAYMENT_LABELS.get(p['method'], p['method'])}</td>
        <td style="padding:4px 8px;text-align:right;">${p['amount']:.2f}</td></tr>"""
        for p in payments
    )
    change_row = (
        f"""<tr><td style="padding:4px 8px;color:#6b7280;">Cambio</td>
        <td style="padding:4px 8px;text-align:right;">${change:.2f}</td></tr>"""
        if change > 0.009 else ""
    )

    tpl = template or {}
    business = tpl.get("business_name") or "Opuntia Den"
    intro = tpl.get("intro_message") or ""
    footer = tpl.get("footer_message") or "Gracias por su compra."
    intro_html = (
        f'<p style="margin:0 0 16px;">{intro}</p>' if intro.strip() else ""
    )

    resend.api_key = settings.resend_api_key
    response = resend.Emails.send({
        "from": FROM_ADDRESS,
        "to": [to_email],
        "subject": f"Ticket de venta #{sale_id} - {business}",
        "html": f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="font-family: sans-serif; color: #1a1a1a; max-width: 480px; margin: 0 auto; padding: 24px;">
  <h2 style="margin-bottom:4px;">{business}</h2>
  <p style="color:#6b7280;margin:0 0 16px;">Ticket de venta #{sale_id} &middot; {date_str}</p>
  {intro_html}
  <table style="width:100%;border-collapse:collapse;font-size:14px;">{rows}</table>
  <table style="width:100%;border-collapse:collapse;font-size:14px;margin-top:8px;">
    <tr><td style="padding:6px 8px;font-weight:bold;">TOTAL</td>
        <td style="padding:6px 8px;text-align:right;font-weight:bold;font-size:16px;">${total:.2f}</td></tr>
    {pay_rows}
    {change_row}
  </table>
  <p style="color:#9ca3af;font-size:12px;margin-top:24px;">{footer}</p>
</body>
</html>
""",
    })
    logger.info("Ticket email sent sale_id=%s to=%s resend_id=%s", sale_id, to_email, response.get("id"))


def send_order_emails(order, customer, notify_email: str = "") -> None:
    """Confirmación al cliente y aviso al negocio. No-op sin RESEND_API_KEY —
    el pedido ya quedó guardado, el correo es un extra."""
    if not settings.resend_api_key:
        logger.warning("Order %s: RESEND_API_KEY missing, skipping emails", order.id)
        return

    rows = "".join(
        f"""<tr>
          <td style="padding:6px 8px;border-bottom:1px solid #e5e7eb;">{item.title}
            {f'<br><span style="color:#6b7280;font-size:12px;">{item.detail}</span>' if item.detail else ''}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #e5e7eb;text-align:right;white-space:nowrap;">
            {float(item.quantity):g}{f' {item.unit}' if item.unit else ''} &times; ${float(item.unit_price):.2f}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #e5e7eb;text-align:right;">${float(item.subtotal):.2f}</td>
        </tr>"""
        for item in order.items
    )
    body = f"""
  <table style="width:100%;border-collapse:collapse;font-size:14px;">{rows}</table>
  <p style="text-align:right;font-size:16px;font-weight:bold;margin:12px 0;">
    Total estimado: ${float(order.total):.2f}</p>
"""
    contact = f"""
  <p style="color:#6b7280;font-size:13px;margin:0;">
    {order.contact_name or customer.name or ''} &middot; {customer.email}
    {f'&middot; {order.contact_phone}' if order.contact_phone else ''}
    {f'<br>{order.address}' if order.address else ''}
    {f'<br><em>{order.notes}</em>' if order.notes else ''}
  </p>"""

    resend.api_key = settings.resend_api_key

    def _send(to_email: str, subject: str, intro: str) -> None:
        resend.Emails.send({
            "from": FROM_ADDRESS,
            "to": [to_email],
            "subject": subject,
            "html": f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"></head>
<body style="font-family: sans-serif; color:#1a1a1a; max-width:480px; margin:0 auto; padding:24px;">
  <h2 style="margin-bottom:4px;">Opuntia Den</h2>
  <p style="color:#6b7280;margin:0 0 16px;">Pedido #{order.id}</p>
  <p style="margin:0 0 16px;">{intro}</p>
  {body}{contact}
</body></html>""",
        })

    try:
        _send(
            customer.email,
            f"Pedido #{order.id} recibido — Opuntia Den",
            "Recibimos tu pedido. Te confirmamos disponibilidad, envío y total en breve; "
            "todavía no se cobra nada.",
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Order %s: customer email failed: %s", order.id, exc)

    if notify_email:
        try:
            _send(notify_email, f"Nuevo pedido #{order.id}", "Entró un pedido nuevo desde el sitio.")
        except Exception as exc:  # noqa: BLE001
            logger.error("Order %s: notify email failed: %s", order.id, exc)
