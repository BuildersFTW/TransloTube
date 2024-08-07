from django.db import models

# Create your models here.
class TaskStatus(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    status = models.TextField()
    context = models.JSONField(null=True)

    def __str__(self):
        return self.task_id

