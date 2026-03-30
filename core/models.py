from django.db import models
from django.contrib.auth.models import User


class ActivityRecord(models.Model):
    """用户活动记录，用于热力图统计"""
    ACTIVITY_TYPES = [
        ('login', '登录'),
        ('read', '阅读'),
        ('write', '写作'),
        ('task_done', '任务完成'),
        ('bookmark', '收藏书签'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_records')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    date = models.DateField()
    count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'activity_type', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'activity_type', 'date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.date}"

    @classmethod
    def record(cls, user, activity_type):
        """快捷记录方法，自动按天聚合"""
        from datetime import date
        today = date.today()
        obj, created = cls.objects.get_or_create(
            user=user,
            activity_type=activity_type,
            date=today,
            defaults={'count': 1}
        )
        if not created:
            cls.objects.filter(pk=obj.pk).update(count=models.F('count') + 1)
