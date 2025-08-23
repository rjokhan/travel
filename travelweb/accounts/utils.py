import logging
import random
from django.conf import settings
from django.core.mail import EmailMessage

log = logging.getLogger("accounts")

def generate_code(n: int = 6) -> str:
    return "".join(random.choices("0123456789", k=n))

def send_signup_code(email: str, code: str) -> tuple[bool, str]:
    """
    Возвращает (ok, err). Не кидает исключений.
    """
    subject = "Код подтверждения регистрации"
    body = (
        f"Ваш код: {code}\n\n"
        "Если вы не запрашивали код, просто игнорируйте это письмо."
    )
    try:
        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[email],
        )
        # важно: не даём исключению убить вьюху
        msg.send(fail_silently=False)
        return True, ""
    except Exception as e:
        log.exception("send_signup_code failed for %s", email)
        return False, str(e)
