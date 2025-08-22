import random
from django.core.mail import send_mail
from django.conf import settings

def generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"

def send_signup_code(email: str, code: str) -> None:
    subject = "Код подтверждения — A CLUB TRAVEL"
    body = (
        f"Ваш код подтверждения: {code}\n\n"
        "Срок действия — 15 минут.\n"
        "Если вы не запрашивали код — просто игнорируйте это письмо."
    )
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
