from django.contrib import admin
from .models import Bookmark, BookmarkCategory


@admin.register(BookmarkCategory)
class BookmarkCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'sort_order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'url', 'is_private', 'is_pinned', 'visit_count', 'created_at']
    list_filter = ['is_private', 'is_pinned', 'category', 'created_at']
    search_fields = ['title', 'url', 'description']
    date_hierarchy = 'created_at'