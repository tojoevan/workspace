from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    # Note URLs
    path('', views.note_list, name='note_list'),
    path('add/', views.note_add, name='note_add'),
    path('<int:pk>/', views.note_detail, name='note_detail'),
    path('<int:pk>/edit/', views.note_edit, name='note_edit'),
    path('<int:pk>/delete/', views.note_delete, name='note_delete'),
    path('<int:pk>/pin/', views.note_toggle_pin, name='note_toggle_pin'),
    path('<int:pk>/archive/', views.note_toggle_archive, name='note_toggle_archive'),
    
    # AI Writing
    path('<int:pk>/ai-write/', views.ai_write, name='ai_write'),
    
    # AI Prompts
    path('ai-prompts/', views.ai_prompt_list, name='ai_prompt_list'),
    path('ai-prompts/add/', views.ai_prompt_add, name='ai_prompt_add'),
    
    # AI Settings
    path('ai-settings/', views.ai_settings, name='ai_settings'),
    
    # Quick Note
    path('quick-note/', views.quick_note_from_article, name='quick_note'),
]
