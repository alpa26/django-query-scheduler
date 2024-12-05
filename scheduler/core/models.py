from django.db import models

class Task(models.Model):
    name = models.CharField(max_length=255)
    resource = models.CharField(max_length=255)
    request = models.CharField(max_length=255)
    task_type = models.CharField(max_length=50)  # 'api' 'db'
    schedule_time = models.DateTimeField()
    repeat_interval = models.CharField(max_length=50, blank=True, null=True)  # 'daily', 'weekly'
    last_run = models.DateTimeField(blank=True, null=True)
    next_run = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class TaskResult(models.Model):
    task = models.ForeignKey(Task, related_name='results', on_delete=models.CASCADE)
    result = models.TextField()
    status = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task.name} - {self.status}"