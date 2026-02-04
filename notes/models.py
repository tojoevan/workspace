from django.db import models
from django.contrib.auth.models import User


class Note(models.Model):
    """笔记"""
    NOTE_TYPES = [
        ('text', '文本'),
        ('markdown', 'Markdown'),
        ('ai', 'AI 生成'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes', verbose_name='用户')
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='markdown', verbose_name='笔记类型')
    tags = models.CharField(max_length=500, blank=True, verbose_name='标签')
    is_pinned = models.BooleanField(default=False, verbose_name='置顶')
    is_archived = models.BooleanField(default=False, verbose_name='归档')
    related_article = models.ForeignKey('news.NewsArticle', on_delete=models.SET_NULL, null=True, blank=True, related_name='notes', verbose_name='关联文章')
    related_rss = models.ForeignKey('rss.RSSArticle', on_delete=models.SET_NULL, null=True, blank=True, related_name='notes', verbose_name='关联 RSS')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '笔记'
        verbose_name_plural = '笔记'
        ordering = ['-is_pinned', '-updated_at']

    def __str__(self):
        return self.title

    def get_tags_list(self):
        """获取标签列表"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class AIWritingPrompt(models.Model):
    """AI 写作提示词模板"""
    PROMPT_TYPES = [
        ('summary', '文章摘要'),
        ('rewrite', '改写'),
        ('expand', '扩写'),
        ('translate', '翻译'),
        ('custom', '自定义'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_prompts', verbose_name='用户')
    name = models.CharField(max_length=100, verbose_name='模板名称')
    prompt_type = models.CharField(max_length=20, choices=PROMPT_TYPES, default='custom', verbose_name='提示词类型')
    prompt_template = models.TextField(verbose_name='提示词模板')
    is_default = models.BooleanField(default=False, verbose_name='默认模板')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = 'AI 写作提示词'
        verbose_name_plural = 'AI 写作提示词'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class AIWritingHistory(models.Model):
    """AI 写作历史"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_writing_history', verbose_name='用户')
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='ai_history', verbose_name='笔记')
    prompt = models.TextField(verbose_name='使用的提示词')
    input_content = models.TextField(verbose_name='输入内容')
    output_content = models.TextField(verbose_name='输出内容')
    model = models.CharField(max_length=50, default='gpt-3.5-turbo', verbose_name='AI 模型')
    tokens_used = models.IntegerField(default=0, verbose_name='使用令牌数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = 'AI 写作历史'
        verbose_name_plural = 'AI 写作历史'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.note.title} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
