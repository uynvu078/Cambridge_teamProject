from django.urls import path
from .views import user_list, user_create, user_update, user_delete
from .views import upload_signature, edit_profile, submitted_forms_list
from .views import generate_filled_pdf, submit_filled_pdf, delete_submitted_form
from . import views

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
]

urlpatterns += [
    path('generate-form/<str:form_type>/', generate_filled_pdf, name='generate_filled_pdf'),
]
