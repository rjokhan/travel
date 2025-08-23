from django.core.mail import send_mail
from django.conf import settings
import logging
log = logging.getLogger(__name__)

def send_signup_code(email, code):
    try:
        send_mail(
            "Код подтверждения — A CLUB TRAVEL",
            f"Ваш код: {code}\nСрок действия: 15 минут.",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=True,  # <-- критично
        )
    except Exception:
        log.exception("send_signup_code crash")
