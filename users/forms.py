from django import forms
from django.contrib.auth import get_user_model

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
