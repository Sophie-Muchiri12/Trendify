"""Outgoing email.

With MAIL_SERVER configured, mail is sent over SMTP. Without it (local development),
each message is saved as a .eml file in instance/outbox/ so you can open verification
and reset links without an email account. Links are never written to the log, because
they work like passwords (A08).
"""
import logging
import os
from email.message import EmailMessage

from flask import current_app
from flask_mail import Message

from extensions import mail
from models.user import utcnow

log = logging.getLogger("trendify")


def send_email(to, subject, body):
    app = current_app
    if app.testing:
        app.extensions.setdefault("test_outbox", []).append({"to": to, "subject": subject, "body": body})
        return
    if app.config.get("MAIL_SERVER"):
        try:
            mail.send(Message(subject=subject, recipients=[to], body=body))
        except Exception:  # noqa: BLE001 - a mail outage must not break the request
            log.exception("Could not send email %r", subject)
        return

    outbox = os.path.join(app.instance_path, "outbox")
    os.makedirs(outbox, mode=0o700, exist_ok=True)
    msg = EmailMessage()
    msg["From"] = app.config["MAIL_DEFAULT_SENDER"]
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    name = f"{utcnow():%Y%m%d-%H%M%S-%f}.eml"
    path = os.path.join(outbox, name)
    with open(path, "wb") as fh:
        fh.write(bytes(msg))
    log.info("Email %r saved to instance/outbox/%s (no MAIL_SERVER configured)", subject, name)


def frontend_link(path, **params):
    from urllib.parse import urlencode

    base = current_app.config["FRONTEND_URL"]
    return f"{base}{path}" + (f"?{urlencode(params)}" if params else "")
