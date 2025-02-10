from django.urls import path
from . import views

urlpatterns = [
    path('process-prompt/', views.process_prompt, name='process_prompt'),
]
