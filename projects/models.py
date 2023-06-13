from colorfield.fields import ColorField
from django.db import models
from django.contrib.auth.models import User, AbstractUser
from pydantic import ValidationError


#
class Project(models.Model):
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="projects")
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['created']


class ChoreStatus(models.Model):
    name = models.CharField(max_length=200, unique=True)
    color = ColorField(max_length=200, null=True, blank=True, unique=True)

    def clean(self):
        existing_color = ChoreStatus.objects.filter(color=self.color).exists()
        if existing_color:
            raise ValidationError("Color already exists in the database.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Chore(models.Model):
    name = models.CharField(max_length=500)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="chores")
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name="chores")
    chore_status = models.ForeignKey(ChoreStatus, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name="chores")


class ProjectUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_users')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_users')
