from django.urls import path
from . import views

urlpatterns = [
    path('process-prompt/', views.process_prompt, name='process_prompt'),
    path('reset-generation/', views.reset_generation, name='reset_generation'),
    path('get-generation-state/', views.get_generation_state, name='get_generation_state'),
]