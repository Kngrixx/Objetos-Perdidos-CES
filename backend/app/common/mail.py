import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from flask import current_app

# Envío de correo para "olvidé mi contraseña".
#   MAIL_MODE=file -> buzón de pruebas local: cada correo se guarda como archivo .eml
#                     en instance/outbox (se abre con doble clic en Outlook/Thunderbird
#                     o con el Bloc de notas).
#   MAIL_MODE=smtp -> se envía por un servidor SMTP real (por ejemplo, smtp4dev o Gmail
#                     con contraseña de aplicación), configurado en el .env.
# El enlace con el token NUNCA se devuelve en el JSON ni se escribe en el log.


def send_email(to_address, subject, body):
    message = EmailMessage()
    message["From"] = current_app.config["MAIL_FROM"]
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    if current_app.config["MAIL_MODE"] == "smtp":
        with smtplib.SMTP(current_app.config["MAIL_SERVER"], current_app.config["MAIL_PORT"], timeout=10) as server:
            if current_app.config["MAIL_USE_TLS"]:
                server.starttls()
            if current_app.config["MAIL_USERNAME"]:
                server.login(current_app.config["MAIL_USERNAME"], current_app.config["MAIL_PASSWORD"])
            server.send_message(message)
        return

    folder = current_app.config["MAIL_OUTBOX_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    safe_address = to_address.replace("@", "_at_")
    file_name = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + "_" + safe_address + ".eml"
    with open(os.path.join(folder, file_name), "wb") as mail_file:
        mail_file.write(bytes(message))
