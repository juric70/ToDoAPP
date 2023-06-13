import datetime

from bootstrap_datepicker_plus.widgets import DatePickerInput
from colorfield.fields import ColorField
from colorfield.widgets import ColorWidget
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.db.models import Prefetch, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from projects.models import Project, Chore, ProjectUser, ChoreStatus
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse


class CustomLoginView(LoginView):
    template_name = 'projects/login.html'
    fields = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('projects')


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        self.fields['username'].label = 'Korisničko ime'
        self.fields['first_name'].label = 'Ime'
        self.fields['last_name'].label = 'Prezime'
        self.fields['email'].label = 'Email'
        self.fields['password2'].label = 'Ponovljena lozinka'
        self.fields['password1'].label = 'Lozinka'


class RegisterPage(FormView):
    template_name = 'projects/register.html'
    form_class = RegisterForm
    redirect_authentificated_user = True
    success_url = reverse_lazy('projects')

    def form_valid(self, form):
        user = form.save()
        if user is not None:
            login(self.request, user)
        return super(RegisterPage, self).form_valid(form)

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('projects')
        return super(RegisterPage, self).get(*args, **kwargs)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'Naslov'
        self.fields['description'].label = 'Opis'


class ProjectList(LoginRequiredMixin, ListView):
    model = Project
    context_object_name = 'projects'

    def get_queryset(self):
        user = self.request.user
        queryset = Project.objects.filter(
            Q(creator=user) | Q(project_users__user=user)
        ).distinct()

        queryset = queryset.prefetch_related(
            Prefetch('chores', queryset=Chore.objects.filter(deadline__gte=datetime.date.today()).order_by('deadline'))
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search_input = self.request.GET.get('search-area') or ''
        if search_input:
            context['projects'] = context['projects'].filter(title__icontains=search_input)

        context['search_input'] = search_input
        context['chore_status'] = ChoreStatus.objects.all()
        return context


class ProjectDetailHome(LoginRequiredMixin, DetailView):
    model = Project
    context_object_name = 'project'
    template_name = 'projects/project.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        today = datetime.date.today()

        upcoming_chores = project.chores.filter(deadline__gte=today).order_by('deadline')
        past_chores = project.chores.filter(deadline__lt=today).order_by('-deadline')

        context['chores'] = list(upcoming_chores) + list(past_chores)

        project_users = list(project.project_users.all())
        context['users'] = project_users

        return context


class ProjectDetail(LoginRequiredMixin, DetailView):
    model = Project
    context_object_name = 'project'
    template_name = 'projects/project.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        # context['chores'] = project.chores.all()
        context['chores'] = project.chores.filter(deadline__gte=datetime.date.today(),
                                                  chore_status__name='pending').order_by('deadline')
        return context


class ProjectCreate(LoginRequiredMixin, CreateView):
    model = Project
    template_name = 'projects/project_create.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super(ProjectCreate, self).form_valid(form)


class ProjectEdit(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    success_url = reverse_lazy('projects')
    template_name = 'projects/project_create.html'

    def test_func(self):
        project = self.get_object()
        project_creator = project.creator
        user = self.request.user
        return user == project_creator


class ProjectDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    context_object_name = 'project'
    success_url = reverse_lazy('projects')
    template_name = 'projects/project_delete.html'

    def test_func(self):
        project = self.get_object()
        project_creator = project.creator
        user = self.request.user
        return user == project_creator


class AddUserToProjectForm(forms.Form):
    search_input = forms.CharField(required=False)

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.fields['users'] = forms.ModelMultipleChoiceField(
            queryset=User.objects.exclude(Q(project_users__project=project) | Q(id=project.creator_id)),
            widget=forms.CheckboxSelectMultiple
        )


class AddUserToProject(FormView):
    template_name = 'projects/project_add_users.html'
    form_class = AddUserToProjectForm
    success_url = 'project/'

    def dispatch(self, request, *args, **kwargs):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id)

        if project.creator != request.user:
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        project_id = self.kwargs['project_id']
        project = Project.objects.get(id=project_id)
        users = form.cleaned_data['users']

        for user in users:
            if not ProjectUser.objects.filter(user=user, project=project).exists():
                ProjectUser.objects.create(user=user, project=project)
        return super().form_valid(form)

    def get_success_url(self):
        project_id = self.kwargs['project_id']
        return reverse_lazy('project', kwargs={'pk': project_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id)
        context['project'] = project
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id)
        kwargs['project'] = project
        return kwargs


class DeleteUserFromProject(DeleteView):
    model = ProjectUser
    context_object_name = 'project_user'
    template_name = 'projects/project_delete_users.html'

    def get_object(self, queryset=None):
        user_id = self.kwargs['user_id']
        project_id = self.kwargs['project_id']
        return get_object_or_404(ProjectUser, user_id=user_id, project_id=project_id)

    def dispatch(self, request, *args, **kwargs):
        project_id = self.kwargs['project_id']
        user_id = self.kwargs['user_id']

        project = get_object_or_404(Project, id=project_id)
        user_to_delete = get_object_or_404(User, id=user_id)

        if request.user != project.creator and request.user != user_to_delete:
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        project_id = self.kwargs['project_id']
        return reverse_lazy('project', kwargs={'pk': project_id})


##Chore

class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = ['name', 'description', 'deadline', 'chore_status']
        widgets = {
            'deadline': DatePickerInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Naslov'
        self.fields['description'].label = 'Opis'
        self.fields['deadline'].label = 'Datum do kada treba obaviti zadatak'
        self.fields['chore_status'].label = 'Status'


class ChoreList(LoginRequiredMixin, ListView):
    model = Chore
    context_object_name = 'chores'
    template_name = 'chores/chores.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class ChoreDetail(LoginRequiredMixin, DetailView):
    model = Chore
    context_object_name = 'chore'
    template_name = 'chores/chore.html'
    form_class = ChoreForm


class ChoreCreate(LoginRequiredMixin, CreateView):
    model = Chore
    template_name = 'chores/create.html'
    form_class = ChoreForm

    def form_valid(self, form):
        form.instance.creator = self.request.user
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id)
        form.instance.project = project
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['chore_status'].label_from_instance = lambda obj: obj.name
        return form

    def get_success_url(self):
        return reverse_lazy('project', kwargs={'pk': self.kwargs['project_id']})


class ChoreEdit(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Chore
    form_class = ChoreForm

    template_name = 'chores/create.html'

    def test_func(self):
        chore = self.get_object()
        project_creator = chore.project.creator
        chore_creator = chore.creator
        user = self.request.user
        return user == project_creator or user == chore_creator

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['chore_status'].label_from_instance = lambda obj: obj.name
        return form

    def get_success_url(self):
        chore = self.get_object()
        project_id = chore.project.id
        return reverse('project', kwargs={'pk': project_id})


class ChoreDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Chore
    context_object_name = 'chores'
    template_name = 'chores/delete.html'

    def test_func(self):
        chore = self.get_object()
        project_creator = chore.project.creator
        chore_creator = chore.creator
        user = self.request.user
        return user == project_creator or user == chore_creator

    def get_success_url(self):
        chore = self.get_object()
        project_id = chore.project.id
        return reverse('project', kwargs={'pk': project_id})


class ChoreStatusUpdate(UpdateView):
    model = Chore
    fields = ['chore_status']
    template_name = 'chores/chore_status_update.html'
    success_url = reverse_lazy('projects')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['chore_status'].label_from_instance = lambda obj: obj.name
        form.fields['chore_status'].label = 'Status zadatka'
        return form

    def form_valid(self, form):
        # Additional logic before saving the form
        return super().form_valid(form)


# Chore status
class ChoreStatusForm(forms.ModelForm):
    color = forms.CharField(widget=ColorWidget(attrs={'class': 'colorpicker'}))

    class Meta:
        model = ChoreStatus
        fields = ['name', 'color']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Naslov'
        self.fields['color'].label = 'Boja'


class ChoreStatusList(ListView):
    model = ChoreStatus
    context_object_name = 'chore_statuses'
    template_name = 'chores/chore_statuses.html'


class ChoreStatusCreateView(CreateView):
    model = ChoreStatus
    form_class = ChoreStatusForm
    template_name = 'chores/chore_status_create.html'
    success_url = reverse_lazy('chore-status-list')
