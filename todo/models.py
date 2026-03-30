from django.db import models
from django.contrib.auth.models import User


class Todo(models.Model):
    """待办事项（含周期性任务）"""
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
    RECURRENCE_CHOICES = [
        ('none', '不重复'),
        ('daily', '每天'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('weekdays', '每个工作日'),
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

    # 周期性任务
    is_recurring = models.BooleanField(default=False, verbose_name='是否重复')
    recurrence_type = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='none', verbose_name='重复类型')
    recurrence_rule = models.JSONField(null=True, blank=True, verbose_name='自定义重复规则')
    last_completed_at = models.DateTimeField(null=True, blank=True, verbose_name='上次完成时间')
    next_due_at = models.DateTimeField(null=True, blank=True, verbose_name='下次到期时间')

    class Meta:
        verbose_name = '待办事项'
        verbose_name_plural = '待办事项'
        ordering = ['-is_pinned', '-priority', '-created_at']

    def __str__(self):
        return self.title

    def mark_completed(self):
        """标记为已完成，并自动生成下一周期任务"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

        # 如果是周期性任务，自动生成下一期
        if self.is_recurring and self.recurrence_type != 'none':
            self._create_next_occurrence()

    def _create_next_occurrence(self):
        """创建下一周期的新任务"""
        from django.utils import timezone
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta

        now = timezone.now()
        next_due = None

        if self.recurrence_type == 'daily':
            next_due = now + timedelta(days=1)
        elif self.recurrence_type == 'weekly':
            next_due = now + timedelta(weeks=1)
        elif self.recurrence_type == 'monthly':
            next_due = now + relativedelta(months=1)
        elif self.recurrence_type == 'weekdays':
            next_due = now + timedelta(days=1)
            while next_due.weekday() >= 5:
                next_due += timedelta(days=1)

        if next_due:
            Todo.objects.create(
                user=self.user,
                title=self.title,
                description=self.description,
                priority=self.priority,
                status='pending',
                due_date=next_due,
                is_recurring=self.is_recurring,
                recurrence_type=self.recurrence_type,
                recurrence_rule=self.recurrence_rule,
                last_completed_at=None,
                next_due_at=next_due,
            )
            self.last_completed_at = now
            self.next_due_at = next_due
            self.save(update_fields=['last_completed_at', 'next_due_at'])

    def save(self, *args, **kwargs):
        # 如果是周期性任务但还没设置 next_due_at，自动设置
        if self.is_recurring and self.recurrence_type != 'none' and not self.next_due_at:
            from django.utils import timezone
            if self.due_date:
                self.next_due_at = self.due_date
            else:
                self.next_due_at = timezone.now()
        super().save(*args, **kwargs)
