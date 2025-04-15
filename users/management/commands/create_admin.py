from django.core.management.base import BaseCommand
from users.models import CustomUser
import os

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if not CustomUser.objects.filter(username='admin').exists():
            CustomUser.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword',
                first_name='Admin',
                last_name='User',
            )
        else:
            return