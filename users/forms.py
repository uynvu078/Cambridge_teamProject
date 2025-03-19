from django import forms
from django.contrib.auth import get_user_model
from .models import Profile, CustomUser

User = get_user_model()

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'is_active']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)  # Get logged-in user
        super().__init__(*args, **kwargs)
        
        # If the logged-in user is NOT an admin, disable role selection
        if user and user.role != "admin":
            self.fields["role"].disabled = True
        else:
            # Admin can assign roles, so allow both 'basicuser' and 'admin'
            self.fields["role"].choices = [
                ("basicuser", "Basic User"),
                ("admin", "Admin")
            ]

# Signature Upload Form
class SignatureUploadForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['signature']

# Profile Form     
class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = Profile
        fields = ['phone_number', 'student_id']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None) 
        super(ProfileForm, self).__init__(*args, **kwargs)

        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email