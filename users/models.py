from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('basicuser', 'Basic User'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='basicuser')
    status = models.BooleanField(default=True)  # True = Active, False = Inactive
    signature = models.ImageField(upload_to="signatures/", null=True, blank=True)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    unit = models.ForeignKey('Unit', null=True, blank=True, on_delete=models.SET_NULL, related_name='users')

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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    comments = models.TextField(blank=True, null=True)
    
    assigned_to = models.ForeignKey(
        CustomUser, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="assigned_forms"
    )

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

User = get_user_model()

class FilledForm(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    form_name = models.CharField(max_length=100)
    filled_pdf = models.FileField(upload_to='filled_forms/')
    version = models.PositiveIntegerField(default=1)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.form_name} (v{self.version})"

class Unit(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subunits')

    def __str__(self):
        return self.name

class Approver(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    is_org_wide = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {'Org-wide' if self.is_org_wide else self.unit.name}"

class Delegation(models.Model):
    approver = models.ForeignKey(Approver, on_delete=models.CASCADE, related_name='delegations')
    delegated_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delegated_approvals')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    def is_active(self):
        now = timezone.now()
        return self.start_date <= now and (self.end_date is None or now <= self.end_date)

    def __str__(self):
        return f"{self.approver.user} → {self.delegated_to} ({'active' if self.is_active() else 'inactive'})"

from django.db.models import Q

def get_active_approver(user):
    now = timezone.now()
    from .models import Delegation  # avoid circular import if needed

    delegation = Delegation.objects.filter(
        delegated_to=user,
        start_date__lte=now
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    ).first()

    if delegation:
        print(f"✅ {user} is acting on behalf of {delegation.approver.user}")
        return delegation.approver.user

    print(f"🔒 No delegation. {user} acts as self.")
    return user

    
rejection_reason = models.TextField(blank=True, null=True)