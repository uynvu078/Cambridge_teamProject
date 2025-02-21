from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from .forms import UserForm
from django.http import HttpResponseForbidden
from functools import wraps
from .models import CustomUser
from django.core.paginator import Paginator


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
    search_query = request.GET.get("search", "")
    role_filter = request.GET.get("role", "")
    sort_by = request.GET.get("sort_by", "username")  # Default sorting by username
    order = request.GET.get("order", "asc")  # Default order is ascending

    users = CustomUser.objects.all()

    if search_query:
        users = users.filter(username__icontains=search_query)
    
    if role_filter:
        users = users.filter(role=role_filter)

    if order == "desc":
        users = users.order_by(f"-{sort_by}")
    else:
        users = users.order_by(sort_by)
        
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get("page")
    users = paginator.get_page(page_number)

    return render(request, "users/user_list.html", {
        "users": users,
        "search_query": search_query,
        "role_filter": role_filter,
        "sort_by": sort_by,
        "order": order
    })

@login_required
@admin_required
def user_create(request):
    if request.method == "POST":
        form = UserForm(request.POST, user=request.user)  
        if form.is_valid():
            user = form.save(commit=False)
            if request.user.role == "admin":  
                user.role = form.cleaned_data["role"]
            else:
                user.role = "basicuser"  
            user.save()
            return redirect("user_list")
    else:
        form = UserForm(user=request.user)  
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
