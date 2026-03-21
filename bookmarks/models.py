from django.db import models
from django.contrib.auth.models import User


class BookmarkCategory(models.Model):
    """书签分类"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmark_categories', verbose_name='用户')
    name = models.CharField(max_length=50, verbose_name='分类名称')
    icon = models.CharField(max_length=50, blank=True, default='fas fa-folder', verbose_name='图标')
    color = models.CharField(max_length=7, default='#3B82F6', verbose_name='颜色')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '书签分类'
        verbose_name_plural = '书签分类'
        ordering = ['sort_order', 'name']
        unique_together = ['user', 'name']

    def __str__(self):
        return self.name


class Bookmark(models.Model):
    """网址书签"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks', verbose_name='用户')
    category = models.ForeignKey(BookmarkCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookmarks', verbose_name='分类')
    title = models.CharField(max_length=200, verbose_name='标题')
    url = models.URLField(verbose_name='网址')
    description = models.TextField(blank=True, verbose_name='备注')
    favicon = models.URLField(blank=True, verbose_name='图标')
    is_private = models.BooleanField(default=True, verbose_name='隐私')
    is_pinned = models.BooleanField(default=False, verbose_name='置顶')
    # 来源信息
    source_type = models.CharField(max_length=20, default='manual', verbose_name='来源类型')  # manual, from_todo, from_rss
    related_todo = models.ForeignKey('todo.Todo', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookmarks', verbose_name='关联待办')
    # 元数据
    visit_count = models.IntegerField(default=0, verbose_name='访问次数')
    last_visited = models.DateTimeField(null=True, blank=True, verbose_name='最后访问')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_bookmarks', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '书签'
        verbose_name_plural = '书签'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title

    def get_domain(self):
        """获取域名"""
        from urllib.parse import urlparse
        return urlparse(self.url).netloc