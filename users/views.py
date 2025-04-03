import os

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.http import FileResponse
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponseForbidden
from users.models import SubmittedForm, SubmittedFormVersion, FilledForm
from users.pdf_utils import fill_pdf
from datetime import datetime
from functools import wraps
from .forms import UserForm, SignatureUploadForm, ProfileForm
from .models import CustomUser, Profile, SubmittedForm
from .pdf_utils import fill_pdf


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
    sort_by = request.GET.get("sort_by", "username")  
    order = request.GET.get("order", "asc")

    users = CustomUser.objects.all()

    if search_query:
        users = users.filter(username__icontains=search_query)
    
    if role_filter:
        users = users.filter(role=role_filter)

    if order == "desc":
        users = users.order_by(f"-{sort_by}")
    else:
        users = users.order_by(sort_by)
        
    paginator = Paginator(users, 10)
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

# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------

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
def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            request.user.first_name = form.cleaned_data["first_name"]
            request.user.last_name = form.cleaned_data["last_name"]
            request.user.email = form.cleaned_data["email"]
            request.user.save()
            form.save()
            return redirect("dashboard")
    else:
        form = ProfileForm(instance=profile, user=request.user)

    return render(request, "users/edit_profile.html", {"form": form})


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

    # Extract user details
    first_name = user.first_name if user.first_name else "Unknown"
    last_name = user.last_name if user.last_name else "Unknown"
    phone = getattr(user.profile, "phone_number", "N/A")
    student_id = getattr(user.profile, "student_id", "N/A")
    email = user.email

    signature_path = user.signature.path if hasattr(user, "signature") and user.signature else None

    user_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "student_id": student_id,
        "signature_path": signature_path,
    }

    print("DEBUG: User Data Sent to fill_pdf:", user_data)

    # unique filename based on username, form type, and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{user.username}_{form_type}_{timestamp}.pdf"

    # Generate filled PDF
    filled_pdf_path = fill_pdf(form_paths[form_type], unique_filename, user_data)

    # Open and properly wrap the file as a Django File object
    with open(os.path.join(settings.MEDIA_ROOT, filled_pdf_path), "rb") as pdf_file:
        pdf_content = pdf_file.read()
        django_file = ContentFile(pdf_content)

        submitted_form = SubmittedForm.objects.filter(user=user, form_type=form_type).order_by('-submitted_at').first()

        if submitted_form:
            submitted_form.pdf_file.save(unique_filename, django_file)
            submitted_form.save()
        else:
            print("WARNING: No existing form entry found!")

    print("DEBUG: PDF stored in database:", submitted_form)

    return FileResponse(
        open(os.path.join(settings.MEDIA_ROOT, filled_pdf_path), "rb"),
        as_attachment=True,
        content_type="application/pdf"
    )


@login_required
def submitted_forms_list(request):
    if request.user.is_superuser or request.user.role == "admin":
        submitted_forms = SubmittedForm.objects.all()  # Admin sees all
    else:
        submitted_forms = SubmittedForm.objects.filter(user=request.user)  # Basic users see only their own

    return render(request, "approval/submitted_forms.html", {"submitted_forms": submitted_forms})



@login_required
def submit_filled_pdf(request, form_type):
    print("DEBUG: submit_filled_pdf() was called with form_type =", form_type)

    user = request.user

    # Check if the form already exists for the user
    existing_form = SubmittedForm.objects.filter(user=user, form_type=form_type).first()
    if existing_form:
        messages.warning(request, "You have already submitted this form. It will not be submitted again.")
        return redirect("submitted_forms")  

    # Process normally if the form doesn't exist
    form_paths = {
        "posthumous_degree": os.path.join(settings.BASE_DIR, "static/pdf_forms/form_a.pdf"),
        "term_withdrawal": os.path.join(settings.BASE_DIR, "static/pdf_forms/form_b.pdf"),
    }

    if form_type not in form_paths:
        messages.error(request, "Invalid form selection.")
        return redirect("submitted_forms")

    user_data = {
        "first_name": user.first_name or "Unknown",
        "last_name": user.last_name or "Unknown",
        "email": user.email,
        "phone": getattr(user.profile, "phone_number", "N/A"),
        "student_id": getattr(user.profile, "student_id", "N/A"),
        "signature_path": user.signature.path if hasattr(user, "signature") and user.signature else None,
    }

    filled_pdf_path = fill_pdf(form_paths[form_type], "output.pdf", user_data)

    with open(os.path.join(settings.MEDIA_ROOT, filled_pdf_path), "rb") as pdf_file:
        pdf_content = pdf_file.read()
        django_file = ContentFile(pdf_content)

        submitted_form = SubmittedForm.objects.create(
            user=user,
            form_type=form_type,
        )
        submitted_form.pdf_file.save(f"{user.student_id}_form.pdf", django_file)
        submitted_form.save()

    messages.success(request, "Form submitted successfully!")
    return redirect("submitted_forms")


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
def delete_submitted_form(request, form_id):
    if request.method == "POST":
        if request.user.is_superuser:  
            submitted_form = get_object_or_404(SubmittedForm, id=form_id)
        else:  
            submitted_form = get_object_or_404(SubmittedForm, id=form_id, user=request.user)

        if submitted_form.pdf_file:
            submitted_form.pdf_file.delete()

        submitted_form.delete()
        messages.success(request, "Form deleted successfully.")
    
    return redirect("submitted_forms")


@login_required
@user_passes_test(lambda u: u.is_superuser)
def form_status(request, form_id):
    form = get_object_or_404(SubmittedForm, id=form_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        comments = request.POST.get("comments", "")
        approver_signature = request.FILES.get("approver_signature")  # Admin signature

        if new_status in ["draft", "pending", "returned", "approved"]:
            form.status = new_status
            form.comments = comments
            form.save()

            # Ensure valid form type mapping to PDFs
            form_templates = {
                "posthumous_degree": "posthumous_degree.pdf",
                "term_withdrawal": "term_withdrawal.pdf",
            }

            if form.form_type in form_templates:
                template_pdf_path = os.path.join(settings.BASE_DIR, "static/pdf_forms", form_templates[form.form_type])

                if os.path.exists(template_pdf_path):
                    user_data = {
                        "first_name": form.user.first_name,
                        "last_name": form.user.last_name,
                        "email": form.user.email,
                        "student_id": getattr(form.user.profile, "student_id", "N/A"),
                        "status": form.get_status_display(),
                    }

                    # Generate filled PDF file
                    output_filename = f"{form.user.username}_{form.form_type}_v{form.versions.count()+1}.pdf"
                    filled_pdf_path = fill_pdf(template_pdf_path, output_filename, user_data)

                    # Save new PDF version
                    if filled_pdf_path:
                        with open(filled_pdf_path, "rb") as pdf_file:
                            django_file = ContentFile(pdf_file.read())
                            submitted_version = SubmittedFormVersion.objects.create(
                                submitted_form=form,
                                pdf_file=django_file,
                                version_number=form.versions.count() + 1,
                            )

                            if new_status == "approved" and approver_signature:
                                submitted_version.approver_signature = approver_signature
                                submitted_version.save()

                        messages.success(request, f"Form status updated to {new_status} and new version saved.")
                    else:
                        messages.warning(request, "Generated PDF file not found. Status updated, but file was not saved.")
                else:
                    messages.error(request, f"Template file for {form.form_type} is missing.")
            else:
                messages.error(request, "Invalid form type.")

        return redirect("submitted_forms")

    return render(request, "approval/form_status.html", {"form": form})

@login_required
def view_submitted_form(request, form_id):
    """Update status to 'Pending' when viewing the submitted form and serve the PDF."""
    submitted_form = get_object_or_404(SubmittedForm, id=form_id)

    # Check if form has an associated PDF file
    if not submitted_form.pdf_file:
        messages.error(request, "No PDF file found for this submission.")
        return redirect("submitted_forms")

    if submitted_form.status == "draft":
        submitted_form.status = "pending"
        submitted_form.save()

    return FileResponse(submitted_form.pdf_file.open("rb"), content_type="application/pdf")

# @login_required
# def upload_filled_pdf(request, form_type):
#     """Handles the uploaded user-filled PDF form submission and updates existing submissions."""
#     user = request.user
#     valid_forms = {
#         "posthumous_degree": "Posthumous Degree",
#         "term_withdrawal": "Term Withdrawal",
#     }

#     if form_type not in valid_forms:
#         messages.error(request, "Invalid form selection.")
#         return redirect("form_selection")

#     if request.method == "POST" and request.FILES.get("filled_pdf"):
#         uploaded_file = request.FILES["filled_pdf"]
#         timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
#         filename = f"{user.username}_{form_type}_{timestamp}.pdf"

#         # --- Save to SubmittedForm (latest version)
#         form_instance, created = SubmittedForm.objects.get_or_create(
#             user=user, form_type=form_type,
#             defaults={"status": "draft"}
#         )

#         # If updating, ensure old file is replaced
#         form_instance.pdf_file.delete(save=False)
#         form_instance.pdf_file = uploaded_file
#         form_instance.pdf_file.name = f"submitted_forms/{filename}"
#         form_instance.status = "pending"
#         form_instance.submitted_at = timezone.now()
#         form_instance.save()
        
#         # Save to FilledForm (version history)
#         version_count = FilledForm.objects.filter(user=user, form_name=form_type).count()
#         FilledForm.objects.create(
#             user=user,
#             form_name=form_type,
#             filled_pdf=uploaded_file,
#             version=version_count + 1,
#         )

#         messages.success(request, "Your form has been submitted and version saved.")
#         return redirect("submitted_forms")

#     messages.error(request, "No file uploaded. Please select a file.")
#     return redirect("form_selection")

@login_required
def upload_filled_pdf(request, form_type):
    user = request.user
    valid_forms = {
        "posthumous_degree": "Posthumous Degree",
        "term_withdrawal": "Term Withdrawal",
    }

    if form_type not in valid_forms:
        messages.error(request, "Invalid form selection.")
        return redirect("form_selection")

    if request.method == "POST" and request.FILES.get("filled_pdf"):
        uploaded_file = request.FILES["filled_pdf"]
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        filename = f"{user.username}_{form_type}_{timestamp}.pdf"
        file_path = f"submitted_forms/{filename}"

        # Save to SubmittedForm
        form_instance, _ = SubmittedForm.objects.get_or_create(
            user=user, form_type=form_type,
            defaults={"status": "draft"}
        )
        form_instance.pdf_file.delete(save=False)
        form_instance.pdf_file.save(file_path, uploaded_file)
        form_instance.status = "pending"
        form_instance.submitted_at = timezone.now()
        form_instance.save()

        # Re-open the saved file for SubmittedFormVersion
        saved_file_path = form_instance.pdf_file.path
        with open(saved_file_path, "rb") as f:
            version_number = SubmittedFormVersion.objects.filter(submitted_form=form_instance).count() + 1
            SubmittedFormVersion.objects.create(
                submitted_form=form_instance,
                pdf_file=ContentFile(f.read(), name=filename),
                version_number=version_number
            )

        messages.success(request, "Your form has been submitted and version saved.")
        return redirect("submitted_forms")

    messages.error(request, "No file uploaded. Please select a file.")
    return redirect("form_selection")

@login_required
def view_form_version(request, version_id):
    version = get_object_or_404(SubmittedFormVersion, id=version_id)

    if request.user != version.submitted_form.user and not request.user.is_superuser and request.user.role != "admin":
        return HttpResponseForbidden("You do not have permission to view this file.")

    return FileResponse(version.pdf_file.open("rb"), content_type="application/pdf")
