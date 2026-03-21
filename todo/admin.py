from django.contrib import admin
from .models import Todo


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'priority', 'is_pinned', 'created_at']
    list_filter = ['status', 'priority', 'is_pinned', 'created_at']
    search_fields = ['title', 'description']
    date_hierarchy = 'created_at'