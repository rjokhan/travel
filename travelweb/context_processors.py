from django.conf import settings

def telegram_settings(request):
    return {"TELEGRAM_BOT_NAME": getattr(settings, "TELEGRAM_BOT_NAME", "")}
