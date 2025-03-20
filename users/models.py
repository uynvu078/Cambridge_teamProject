from django.db import models
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
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    student_id = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

class SubmittedForm(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending Review"),
        ("returned", "Returned for Changes"),
        ("approved", "Approved"),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    form_type = models.CharField(max_length=50)  
    pdf_file = models.FileField(upload_to='submitted_forms/%Y/%m/%d/', null=True, blank=True)  
    submitted_at = models.DateTimeField(auto_now_add=True)  
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.form_type} ({self.status})"

class SubmittedFormVersion(models.Model):
    submitted_form = models.ForeignKey(SubmittedForm, on_delete=models.CASCADE, related_name="versions")
    pdf_file = models.FileField(upload_to="submitted_forms/%Y/%m/%d/")
    version_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    approver_signature = models.ImageField(upload_to="approver_signatures/%Y/%m/%d/", null=True, blank=True)

    class Meta:
        unique_together = ('submitted_form', 'version_number')

    def save(self, *args, **kwargs):
        """Auto-increments version number if not set"""
        if not self.version_number:
            last_version = SubmittedFormVersion.objects.filter(submitted_form=self.submitted_form).order_by("-version_number").first()
            self.version_number = (last_version.version_number + 1) if last_version else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Version {self.version_number} of {self.submitted_form.form_type}"
