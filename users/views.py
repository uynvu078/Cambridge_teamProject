from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from .forms import UserForm, SignatureUploadForm
from django.http import HttpResponseForbidden
from functools import wraps
from .models import CustomUser
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect
from .pdf_utils import fill_pdf
import os
from django.conf import settings
from django.http import FileResponse



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

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@user_passes_test(is_admin)
def deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_active:
        user.is_active = False
        user.save()
        messages.success(request, f'User {user.username} has been deactivated.')
    else:
        messages.info(request, f'User {user.username} is already deactivated.')
    return redirect('user_list')

@user_passes_test(is_admin)
def reactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user.is_active:
        user.is_active = True
        user.save()
        messages.success(request, f'User {user.username} has been reactivated.')
    else:
        messages.info(request, f'User {user.username} is already active.')
    return redirect('user_list')

@login_required
def upload_signature(request):
    """Allows users to upload their signature."""
    if request.method == "POST":
        form = SignatureUploadForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Signature uploaded successfully!")
            return redirect("dashboard")
    else:
        form = SignatureUploadForm(instance=request.user)

    return render(request, "users/upload_signature.html", {"form": form})


@login_required
def form_selection(request):
    return render(request, 'form_selection.html')

@login_required
def generate_filled_pdf(request, form_type):
    print("DEBUG: generate_filled_pdf() was called with form_type =", form_type)

    form_paths = {
        "posthumous_degree": os.path.join(settings.BASE_DIR, "static/pdf_forms/form_a.pdf"),
        "term_withdrawal": os.path.join(settings.BASE_DIR, "static/pdf_forms/form_b.pdf"),
    }

    if form_type not in form_paths:
        print("DEBUG: Invalid form type selected:", form_type)
        return HttpResponse("Invalid form selection.", status=400)

    user = request.user

    # Fixing missing user details
    first_name = user.first_name if user.first_name else "Unknown"
    last_name = user.last_name if user.last_name else "Unknown"
    phone = user.profile.phone_number if hasattr(user, "profile") and user.profile.phone_number else "N/A"
    student_id = user.profile.student_id if hasattr(user, "profile") and user.profile.student_id else "N/A"
    signature_path = user.signature.path if hasattr(user, "signature") and user.signature else None

    user_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": user.email,
        "phone": phone,
        "student_id": student_id,
        "signature_path": signature_path,
    }

    print("DEBUG: User Data Sent to fill_pdf:", user_data)

    filled_pdf_path = fill_pdf(form_paths[form_type], "output.pdf", user_data)

    return FileResponse(open(os.path.join(settings.MEDIA_ROOT, filled_pdf_path), "rb"), as_attachment=True, content_type="application/pdf")
