from django.urls import path
from .views import user_list, user_create, user_update, user_delete
from .views import upload_signature, edit_profile, submitted_forms_list, form_status
from .views import generate_filled_pdf, submit_filled_pdf, delete_submitted_form
from .views import view_submitted_form , view_form_version
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

]

urlpatterns += [
    path('generate-form/<str:form_type>/', generate_filled_pdf, name='generate_filled_pdf'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)