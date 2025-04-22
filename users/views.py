import os
import shutil

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
from .forms import UserForm, SignatureUploadForm, ProfileForm, Approver
from .models import CustomUser, Profile, SubmittedForm, Approver
from .pdf_utils import fill_pdf
from users.latex_utils import fill_latex_template
from django.http import HttpResponse

# Admin views
def admin_required(view_func):
    """Decorator to restrict accesss to admin users only."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            return HttpResponseForbidden("You do not have permission to view this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# User List Views and Filter
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

# Creating User
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

# Updating User
@login_required
@admin_required
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserForm(request.POST, instance=user, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully!")
            return redirect('user_list')
    else:
        form = UserForm(instance=user)
    return render(request, 'users/user_form.html', {'form': form})

# Deleting User
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

# Deactivate User
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

# Reactivate User
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

# Upload Signature
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


# Selecting Form
@login_required
def form_selection(request):
    return render(request, 'form_selection.html')

# Updating information for each user
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

# Filled the pdf
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

# Admin can access all submitted forms
@login_required
def submitted_forms_list(request):
    if request.user.is_superuser or request.user.role == "admin":
        submitted_forms = SubmittedForm.objects.all()  # Admin sees all
    else:
        submitted_forms = SubmittedForm.objects.filter(user=request.user)  # Basic users see only their own

    return render(request, "approval/submitted_forms.html", {"submitted_forms": submitted_forms})


# User can submit their auto filled pdf
@login_required
def submit_filled_pdf(request, form_type):
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
        unit = user.unit
        approver = Approver.objects.filter(unit=unit).first()

        if not approver:
            approver = Approver.objects.filter(is_org_wide=True).first()
        if approver:
            submitted_form.assigned_to = approver.user
        else:
            messages.warning(request, "No approver available for your unit. Your form will remain unassigned.")

        # Save uploaded PDF
        submitted_form.pdf_file.save(f"{user.student_id}_form.pdf", django_file)
        submitted_form.save()

    messages.success(request, "Form submitted successfully!")
    return redirect("submitted_forms")


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

# Deleting the submitted form. Admin can delete all forms, user can only delete their own form
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

# Approved forms/Admin checking the form status
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

#Viewing the pdf
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

# Function to upload the filled pdf and stored it in the database to review
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

# View different form versions
@login_required
def view_form_version(request, version_id):
    version = get_object_or_404(SubmittedFormVersion, id=version_id)

    if request.user != version.submitted_form.user and not request.user.is_superuser and request.user.role != "admin":
        return HttpResponseForbidden("You do not have permission to view this file.")

    return FileResponse(version.pdf_file.open("rb"), content_type="application/pdf")

@login_required
def generate_latex_form(request, form_type):
    template_map = {
        "posthumous_degree": "form_a.tex",
        "term_withdrawal": "form_b.tex",
    }

    if form_type not in template_map:
        return HttpResponse("Invalid form type.", status=400)

    user = request.user
    profile = getattr(user, "profile", None)

    signature_filename = ""
    if user.signature:
        signature_path = user.signature.path  # stored in media/signatures/
        signature_filename = os.path.basename(signature_path)

        latex_sig_dir = os.path.join(settings.BASE_DIR, "users", "latex_templates", "signatures")
        os.makedirs(latex_sig_dir, exist_ok=True)

        destination = os.path.join(latex_sig_dir, signature_filename)
        shutil.copyfile(signature_path, destination)

    context = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": profile.phone_number if profile else "",
        "student_id": profile.student_id if profile else "",
        "program": "Computer Science",
        "career": "Graduate",
        "term": "Spring",
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "signature_filename": signature_filename,
    }

    template_path = os.path.join(settings.BASE_DIR, "users", "latex_templates", template_map[form_type])
    filename = f"{user.username}_{form_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    filled_pdf_path = fill_latex_template(template_path, context, filename)

    return FileResponse(open(filled_pdf_path, "rb"), content_type="application/pdf")

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Approver, Delegation, SubmittedForm

@login_required
def delegated_approval_dashboard(request):
    current_user = request.user
    view_type = request.GET.get("view", "my")
    now = timezone.now()

    # Determine the actual approver (in case of delegation)
    actual_approver = get_active_approver(current_user)
    user_is_approver = Approver.objects.filter(user=actual_approver).exists()

    if not user_is_approver:
        messages.warning(request, "🚫 You are not authorized to approve forms.")
        return redirect('submitted_forms')

    approver = Approver.objects.get(user=actual_approver)
    is_org_wide = approver.is_org_wide

    if view_type == "my":
        if current_user == actual_approver:
            # Approver: show other users' submissions in their unit
            if is_org_wide:
                forms = SubmittedForm.objects.filter(status='pending').exclude(user=current_user)
            else:
                forms = SubmittedForm.objects.filter(status='pending', user__unit=approver.unit).exclude(user=current_user)
        else:
            # Delegate: show their own submissions only
            forms = SubmittedForm.objects.filter(status='pending', user=current_user)

    elif view_type == "delegated":
        if current_user == actual_approver:
            # Approver: show their own submissions
            forms = SubmittedForm.objects.filter(status='pending', user=current_user)
        else:
            # Delegate: only show forms submitted by the actual approver (not others)
            forms = SubmittedForm.objects.filter(status='pending', user=actual_approver).exclude(user=current_user)
    else:
        forms = SubmittedForm.objects.none()

    unassigned_count = SubmittedForm.objects.filter(status='pending', assigned_to__isnull=True).count()

    return render(request, 'approval_dashboard.html', {
        'forms': forms,
        'actual_approver': actual_approver,
        'user_is_approver': user_is_approver,
        'unassigned_count': unassigned_count,
        'view_type': view_type,
        'user_is_admin': request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'
    })

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ApproverForm

@login_required
def approve_form(request, form_id):
    current_user = request.user
    form = get_object_or_404(SubmittedForm, id=form_id)

    # Prevent self-approval
    if form.user == current_user:
        return HttpResponseForbidden("You cannot approve your own submitted form.")

    # Check if user is allowed to approve this form
    actual_approver = get_active_approver(current_user)

    try:
        approver = Approver.objects.get(user=actual_approver)
        if approver.is_org_wide or (form.user.unit == approver.unit):
            form.status = 'approved'
            form.save()
            messages.success(request, f"✅ Form '{form.form_type}' approved successfully.")
        else:
            return HttpResponseForbidden("You are not authorized to approve this form.")
    except Approver.DoesNotExist:
        return HttpResponseForbidden("You are not an approver.")

    return redirect(reverse('approval_dashboard') + "?view=my")


@login_required
def reject_form(request, form_id):
    current_user = request.user
    form = get_object_or_404(SubmittedForm, id=form_id)

    # Prevent self-rejection
    if form.user == current_user:
        return HttpResponseForbidden("You cannot reject your own submitted form.")
    
    actual_approver = get_active_approver(current_user)

    try:
        approver = Approver.objects.get(user=actual_approver)
        if not (approver.is_org_wide or (form.user.unit == approver.unit)):
            return HttpResponseForbidden("You are not authorized to reject this form.")
    except Approver.DoesNotExist:
        return HttpResponseForbidden("You are not an approver.")

    if request.method == "POST":
        reason = request.POST.get("reason")
        form.status = "returned"
        form.rejection_reason = reason
        form.save()
        messages.warning(request, f"⚠️ Form '{form.form_type}' was returned with a comment.")
        return redirect(reverse('approval_dashboard') + "?view=my")

    return render(request, 'reject_form.html', {'form': form})

@login_required
def manage_approvers(request):
    if not (request.user.is_superuser or request.user.role == "admin"):
        messages.warning(request, "You are not authorized to manage approvers.")
        return redirect("submitted_forms")

    if request.method == "POST":
        form = ApproverForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            # Prevent duplicate approver entries
            if Approver.objects.filter(user=user).exists():
                messages.warning(request, f"{user} is already an approver.")
            else:
                form.save()
                messages.success(request, f"{user} added as an approver.")
            return redirect("manage_approvers")
    else:
        form = ApproverForm()

    approvers = Approver.objects.select_related('user', 'unit')
    return render(request, "manage_approvers.html", {
        "form": form,
        "approvers": approvers
    })

@login_required
def remove_approver(request, approver_id):
    if not (request.user.is_superuser or request.user.role == "admin"):
        messages.warning(request, "You are not authorized to remove approvers.")
        return redirect("submitted_forms")

    approver = get_object_or_404(Approver, id=approver_id)
    approver.delete()
    messages.success(request, f"{approver.user} removed from approvers.")
    return redirect("manage_approvers")

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from .models import SubmittedForm, Unit

@login_required
def reporting_dashboard(request):
    units = Unit.objects.all()
    if not (request.user.is_superuser or request.user.role == "admin"):
        messages.warning(request, "You are not authorized to view reports.")
        return redirect("dashboard")

    forms = SubmittedForm.objects.select_related("user", "user__unit").all()

    # Filtering
    status_filter = request.GET.get("status", "")
    unit_filter = request.GET.get("unit", "")

    if status_filter:
        forms = forms.filter(status=status_filter)
    if unit_filter:
        forms = forms.filter(user__unit__id=unit_filter)

    # Summary stats
    summary = {
        "total": forms.count(),
        "pending": forms.filter(status="pending").count(),
        "approved": forms.filter(status="approved").count(),
        "returned": forms.filter(status="returned").count(),
    }

    units = Unit.objects.all()

    return render(request, "reporting_dashboard.html", {
        "forms": forms,
        "units": units,
        "summary": summary,
        "status_filter": status_filter,
        "unit_filter": unit_filter,
    })

import csv
from django.http import HttpResponse
from .models import SubmittedForm

@login_required
def download_approval_report(request):
    if not request.user.is_superuser and request.user.role != "admin":
        messages.warning(request, "You are not authorized to download reports.")
        return redirect('reporting_dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="approval_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['User', 'Unit', 'Form Type', 'Status', 'Submitted At', 'Assigned To'])

    for form in SubmittedForm.objects.all():
        writer.writerow([
            form.user.username,
            form.user.unit.name if form.user.unit else "N/A",
            form.form_type,
            form.get_status_display(),
            form.submitted_at.strftime('%Y-%m-%d %H:%M'),
            form.assigned_to.username if form.assigned_to else "Unassigned"
        ])

    return response

from .forms import DelegationForm
from .models import Delegation, Approver

@login_required
def manage_delegation(request):
    user = request.user

    try:
        approver = Approver.objects.get(user=user)
    except Approver.DoesNotExist:
        messages.error(request, "You are not an approver.")
        return redirect('dashboard')

    delegations = approver.delegations.all()

    if request.method == "POST":
        form = DelegationForm(request.POST)
        if form.is_valid():
            delegation = form.save(commit=False)
            delegation.approver = approver
            delegation.save()
            messages.success(request, f"Delegated to {delegation.delegated_to} from {delegation.start_date} to {delegation.end_date}")
            return redirect("manage_delegation")
    else:
        form = DelegationForm()

    return render(request, "manage_delegation.html", {
        "form": form,
        "delegations": delegations
    })


@login_required
def remove_delegation(request, delegation_id):
    try:
        delegation = Delegation.objects.get(id=delegation_id, approver__user=request.user)
        delegation.delete()
        messages.success(request, "Delegation removed successfully.")
    except Delegation.DoesNotExist:
        messages.error(request, "Delegation not found or you don't have permission.")
    return redirect("manage_delegation")

from .models import get_active_approver

@login_required
def submitted_forms_view(request):
    submitted_forms = SubmittedForm.objects.filter(user=request.user).order_by('-submitted_at')

    return render(request, "submitted_forms.html", {
        "submitted_forms": submitted_forms
    })
    
from django.shortcuts import render
from .models import Unit

def unit_tree_view(request):
    root_units = Unit.objects.filter(parent=None)
    return render(request, 'unit_tree.html', {'root_units': root_units})