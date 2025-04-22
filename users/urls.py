from django.urls import path
from .views import user_list, user_create, user_update, user_delete
from .views import upload_signature, edit_profile, submitted_forms_list, form_status
from .views import generate_filled_pdf, submit_filled_pdf, delete_submitted_form
from .views import view_submitted_form , view_form_version, delegated_approval_dashboard
from .views import manage_delegation, remove_delegation, unit_tree_view
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', user_list, name="user_list"),  # List all users
    path('create/', user_create, name="user_create"),  # Create a new user
    path('<int:pk>/edit/', user_update, name="user_update"),  # Edit user
    path('<int:pk>/delete/', user_delete, name="user_delete"),  # Delete user
    path('deactivate/<int:user_id>/', views.deactivate_user, name='deactivate_user'),
    path('reactivate/<int:user_id>/', views.reactivate_user, name='reactivate_user'),
    
    path('upload-signature/', upload_signature, name="upload_signature"),
    path('forms/', views.form_selection, name='form_selection'),
    path("edit-profile/", edit_profile, name="edit_profile"),
    path("submitted-forms/", submitted_forms_list, name="submitted_forms"),
    path("submit-filled-pdf/<str:form_type>/", submit_filled_pdf, name="submit_filled_pdf"),
    path("delete-submitted-form/<int:form_id>/", delete_submitted_form, name="delete_submitted_form"),
    path('view-submitted-form/<int:form_id>/', view_submitted_form, name='view_submitted_form'),
    
    path("update-form-status/<int:form_id>/", form_status, name="form_status"),
    path("upload-filled-pdf/<str:form_type>/", views.upload_filled_pdf, name="upload_filled_pdf"),
    path('form-version/<int:version_id>/', view_form_version, name='view_form_version'),
    path('generate-latex-form/<str:form_type>/', views.generate_latex_form, name='generate_latex_form'),
    path('approvals/', delegated_approval_dashboard, name='approval_dashboard'),
    path('approve/<int:form_id>/', views.approve_form, name='approve_form'),
    path('reject/<int:form_id>/', views.reject_form, name='reject_form'),
    path('manage-approvers/', views.manage_approvers, name='manage_approvers'),
    path('remove-approver/<int:approver_id>/', views.remove_approver, name='remove_approver'),
]

urlpatterns += [
    path('generate-form/<str:form_type>/', generate_filled_pdf, name='generate_filled_pdf'),
    path("reporting/", views.reporting_dashboard, name="reporting_dashboard"),
    path('reporting/download/', views.download_approval_report, name='download_approval_report'),
    path("delegate-approval/", manage_delegation, name="manage_delegation"),
    path("delegate-approval/remove/<int:delegation_id>/", remove_delegation, name="remove_delegation"),
    path("unit-hierarchy/", unit_tree_view, name="unit_tree_view"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)