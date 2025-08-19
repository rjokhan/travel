from django.core.management.base import BaseCommand
from travelapp.models import Country
import pycountry


class Command(BaseCommand):
    help = "Синхронизирует все страны мира в базу (Country)"

    def handle(self, *args, **kwargs):
        self.stdout.write("Синхронизация стран начата...")

        for country in pycountry.countries:
            Country.objects.get_or_create(
                iso2=country.alpha_2,
                defaults={"name": country.name}
            )

        self.stdout.write(self.style.SUCCESS("✅ Все страны добавлены в базу!"))
