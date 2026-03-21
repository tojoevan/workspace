from django.urls import path
from . import views

app_name = 'todo'

urlpatterns = [
    # Todo 列表与CRUD
    path('', views.todo_list, name='todo_list'),
    path('add/', views.todo_add, name='todo_add'),
    path('quick-add/', views.todo_quick_add, name='todo_quick_add'),
    path('<int:pk>/', views.todo_detail, name='todo_detail'),
    path('<int:pk>/edit/', views.todo_edit, name='todo_edit'),
    path('<int:pk>/delete/', views.todo_delete, name='todo_delete'),
    path('<int:pk>/complete/', views.todo_toggle_complete, name='todo_toggle_complete'),
    path('<int:pk>/pin/', views.todo_toggle_pin, name='todo_toggle_pin'),

    # 从Todo转换为书签
    path('<int:pk>/to-bookmark/', views.todo_to_bookmark, name='todo_to_bookmark'),
]