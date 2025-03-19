from django.urls import path
from .views import user_list, user_create, user_update, user_delete, upload_signature
from . import views
from .views import generate_filled_pdf 

urlpatterns = [
    path('', user_list, name="user_list"),  # List all users
    path('create/', user_create, name="user_create"),  # Create a new user
    path('<int:pk>/edit/', user_update, name="user_update"),  # Edit user
    path('<int:pk>/delete/', user_delete, name="user_delete"),  # Delete user
    path('deactivate/<int:user_id>/', views.deactivate_user, name='deactivate_user'),
    path('reactivate/<int:user_id>/', views.reactivate_user, name='reactivate_user'),
    
    path('upload-signature/', upload_signature, name="upload_signature"), #signature route
    path('forms/', views.form_selection, name='form_selection'),
]

urlpatterns += [
    path('generate-form/<str:form_type>/', generate_filled_pdf, name='generate_filled_pdf'),
]
