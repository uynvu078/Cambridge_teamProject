from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from .forms import UserForm
from django.http import HttpResponseForbidden
from functools import wraps

def admin_required(view_func):
    """Decorator to restrict accesss to admin users only."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            return HttpResponseForbidden("You do not have permission to view this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


User = get_user_model()

@login_required
def user_list(request):
    users = User.objects.all()
    return render(request, 'users/user_list.html', {'users': users})

@login_required
@admin_required
def user_create(request):
    if request.method == "POST":
        form = UserForm(request.POST, user=request.user)  # logged-in user
        if form.is_valid():
            user = form.save(commit=False)
            if request.user.role == "admin":  # nly admins can set roles
                user.role = form.cleaned_data["role"]
            else:
                user.role = "basicuser"  # Default role for non-admins
            user.save()
            return redirect("user_list")
    else:
        form = UserForm(user=request.user)  # logged-in user
    return render(request, "users/user_form.html", {"form": form})

@login_required
@admin_required
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserForm(request.POST, instance=user, user=request.user) #Pass user to forms
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully!")
            return redirect('user_list')
    else:
        form = UserForm(instance=user)
    return render(request, 'users/user_form.html', {'form': form})

@login_required
@admin_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user.delete()
        messages.success(request, "User deleted successfully!")
        return redirect('user_list')
    return render(request, 'users/user_confirm_delete.html', {'user': user})
