from django.urls import path
from . import views

app_name = 'medical_records'

urlpatterns = [
    path('pets/', views.pet_list, name='pet_list'),
    path('pets/add/', views.add_pet, name='add_pet'),
    path('pets/<int:pk>/', views.pet_detail, name='pet_detail'),
    path('pets/<int:pet_pk>/add-record/', views.add_medical_record, name='add_medical_record'),
    path('pets/<int:pet_pk>/vaccinate/', views.add_vaccination, name='add_vaccination'),
    path('records/<int:pk>/', views.medical_record_detail, name='record_detail'),
    path('vaccinations/', views.vaccination_list, name='vaccination_list'),
    path('vaccinations/<int:pk>/administer/', views.administer_vaccination, name='administer_vaccination'),
]
