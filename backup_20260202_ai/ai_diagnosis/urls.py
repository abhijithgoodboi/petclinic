from django.urls import path
from . import views

app_name = 'ai_diagnosis'

urlpatterns = [
    path('', views.diagnosis_home, name='home'),
    path('upload/', views.upload_image, name='upload'),
    path('result/<int:pk>/', views.diagnosis_result, name='result'),
    path('result/<int:pk>/review/', views.review_diagnosis, name='review'),
    path('history/', views.diagnosis_history, name='history'),
]
