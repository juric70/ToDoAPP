from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import ProjectList, ProjectDetail, ProjectCreate, ProjectEdit, ProjectDelete, CustomLoginView, RegisterPage, \
    ChoreDelete, ChoreDetail, ChoreEdit, ChoreCreate, ChoreList, ChoreStatusUpdate, AddUserToProject, ProjectDetailHome, \
    DeleteUserFromProject, ChoreStatusList, ChoreStatusCreateView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(next_page='login'), name="logout"),
    path('register', RegisterPage.as_view(), name='register'),

    path('', ProjectList.as_view(), name='projects'),
    path('project_create/', ProjectCreate.as_view(), name='project-create'),
    path('project_edit/<int:pk>', ProjectEdit.as_view(), name='project-edit'),
    path('project/<int:pk>', ProjectDetailHome.as_view(), name='project'),
    path('project_delete/<int:pk>', ProjectDelete.as_view(), name='project-delete'),

    path('chores', ChoreList.as_view(), name='chores'),
    path('chore_create/<int:project_id>', ChoreCreate.as_view(), name='chore-create'),
    path('chore_edit/<int:pk>', ChoreEdit.as_view(), name='chore-edit'),
    path('chore_status/<int:pk>', ChoreStatusUpdate.as_view(), name='chore-status'),
    path('chore/<int:pk>', ChoreDetail.as_view(), name='chore'),
    path('chore_delete/<int:pk>', ChoreDelete.as_view(), name='chore-delete'),

    path('project_users/<int:project_id>', AddUserToProject.as_view(), name='project-users'),
    path('project/<int:project_id>/delete_user/<int:user_id>/', DeleteUserFromProject.as_view(), name='delete_user'),

    path('chore_status', ChoreStatusList.as_view(), name='chore-status-list'),
    path('status_create', ChoreStatusCreateView.as_view(), name='chore-status-create'),

]
