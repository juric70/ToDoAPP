from django.contrib import admin
from .models import Project, Chore, ChoreStatus, ProjectUser

admin.site.register(Project)
admin.site.register(Chore)
admin.site.register(ChoreStatus)
admin.site.register(ProjectUser)

