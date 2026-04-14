from flask_mail import Message
from flask import render_template, current_app
from app import mail


def send_email(subject, recipients, template, **kwargs):
    msg = Message(
        subject=subject,
        recipients=recipients,
        sender=current_app.config.get('MAIL_DEFAULT_SENDER')
    )

    msg.html = render_template(template, **kwargs)
    mail.send(msg)