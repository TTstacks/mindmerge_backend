from django.db import models
from django.conf import settings
from users.utilities import safe_file_name, SafeFileName

# Create your models here.
class Tag(models.Model):
    name = models.CharField(max_length=35)


class Project(models.Model):
    class Status(models.IntegerChoices):
        PUBLIC = 1
        PRIVATE = 2

    image = models.ImageField(upload_to=safe_file_name('projects'), default='projects/default.jpg')
    title = models.CharField(max_length=255)
    description = models.TextField()
    tags = models.ManyToManyField(Tag)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_project_set")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Membership', related_name="member_project_set")
    privacy = models.IntegerField(choices = Status, default = 1)

    class Meta:
        ordering = ['id']



class Membership(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 1
        ACCEPTED = 2
        REJECTED = 3
    
    status = models.IntegerField(choices=Status, default=1)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_membership_set')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_membership_set")
    join_request_text = models.TextField()


class Message(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_message_set')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_message_set")
    text = models.TextField(null=True)
    media = models.FileField(upload_to=safe_file_name('messages'), null=True)
    time = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='message_parent')

    class Meta:
        indexes = [
            models.Index(fields=['project', 'id']),
            models.Index(fields=['user']),
        ]



class WebhookEvent(models.Model):
    idempotency_key = models.CharField(max_length=255, unique=True)
