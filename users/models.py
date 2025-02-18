from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('basicuser', 'Basic User'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='basicuser')
    status = models.BooleanField(default=True)  # True = Active, False = Inactive

    def __str__(self):
        return self.username

