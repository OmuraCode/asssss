from django.db import models
from django.utils import timezone

# Create your models here.

class Threads(models.Model):
    user_id = models.CharField(max_length=255, null=True, blank=True)
    thread_id = models.CharField(max_length=100, null=True, blank=True)
    is_active_session = models.BooleanField(default=True)
    chanel = models.CharField(max_length=100, null=True, blank=True)
    # conversation = models.JSONField()
    last_activity_time = models.DateTimeField(default=timezone.now)
