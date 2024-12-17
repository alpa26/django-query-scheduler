from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Task(models.Model):
    TASK_TYPE_CHOICES = [
        ('api', 'API'),
        ('db', 'Database'),
    ]

    REPEAT_INTERVAL_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('hourly', 'Hourly'),
    ]

    name = models.CharField(max_length=255)
    resource = models.CharField(max_length=255)
    request = models.CharField(max_length=255)
    task_type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES)
    schedule_time = models.DateTimeField()
    repeat_interval = models.CharField(max_length=50,
                                       choices=REPEAT_INTERVAL_CHOICES,
                                       blank=True, null=True)
    last_run = models.DateTimeField(blank=True, null=True)
    next_run = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    table_name = models.CharField(max_length=255, null=True)
    is_task_created = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    from .views import handle_task_creation
    if created and not instance.is_task_created:
        handle_task_creation(instance)
        instance.table_name = f"{instance.table_name}.xlsx"
        instance.is_task_created = True
        instance.save()


class TaskResult(models.Model):
    task = models.ForeignKey(Task, related_name='results',
                             on_delete=models.CASCADE)
    result = models.TextField()
    status = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task.name} - {self.status}"
