from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('basicuser', 'Basic User'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='basicuser')
    status = models.BooleanField(default=True)  # True = Active, False = Inactive
    signature = models.ImageField(upload_to="signatures/", null=True, blank=True)

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    student_id = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
    
class SubmittedForm(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    form_type = models.CharField(max_length=100)  
    pdf_file = models.FileField(upload_to='submitted_forms/')  
    submitted_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f"{self.user.username} - {self.form_type} ({self.submitted_at})"