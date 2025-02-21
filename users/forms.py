from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'is_active']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None) #Get logged-in user
        super().__init__(*args, **kwargs)
        if user and user.role != "admin":
            self.fields["role"].disabled = True #Prevent non-admins form changing roles
