from django.core.management.base import BaseCommand
from library.models import User

class Command(BaseCommand):
    help = 'Create a library admin account'

    def handle(self, *args, **options):
        email    = 'admin@unilib.com'
        password = 'admin1234'
        name     = 'Library Admin'

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'Admin already exists: {email}'))
            return

        User.objects.create_admin(email=email, name=name, password=password)
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Admin created!\n   Email:    {email}\n   Password: {password}\n'
        ))
