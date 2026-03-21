from django.db import models
from django.contrib.auth.models import User


class Todo(models.Model):
    """待办事项"""
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
    ]

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos', verbose_name='用户')
    title = models.CharField(max_length=200, verbose_name='标题')
    description = models.TextField(blank=True, verbose_name='描述')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='优先级')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='截止时间')
    is_pinned = models.BooleanField(default=False, verbose_name='置顶')
    related_bookmark = models.ForeignKey('bookmarks.Bookmark', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_todos', verbose_name='关联书签')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        verbose_name = '待办事项'
        verbose_name_plural = '待办事项'
        ordering = ['-is_pinned', '-priority', '-created_at']

    def __str__(self):
        return self.title

    def mark_completed(self):
        """标记为已完成"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()