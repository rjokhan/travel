import random
from django.core.mail import send_mail
from django.conf import settings

def generate_code() -> str:
    # шестизначный код с лидирующими нулями
    return f"{random.randint(0, 999999):06d}"

def send_signup_code(email: str, code: str) -> None:
    subject = "Ваш код подтверждения — A CLUB TRAVEL"
    message = (
        f"Код подтверждения: {code}\n\n"
        "Он действителен 15 минут. Если это были не Вы — просто игнорируйте письмо."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@localhost"),
        recipient_list=[email],
        fail_silently=False,
    )
