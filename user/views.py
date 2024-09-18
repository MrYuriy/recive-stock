from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View, generic

from user.models import User

from .forms import UserCreationForm, UserSearchForm, UserUpdateForm


# Create your views here.


class UserListView(LoginRequiredMixin, generic.ListView):
    model = User

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)

        username = self.request.GET.get("username", "")
        context["search_form"] = UserSearchForm(initial={"username": username})
        return context

    def get_queryset(self):
        queryset = User.objects.all()
        form = UserSearchForm(self.request.GET)

        if form.is_valid():
            return queryset.filter(username__icontains=form.cleaned_data["username"])
        return queryset


class UserCreateView(LoginRequiredMixin, generic.CreateView):
    model = User
    form_class = UserCreationForm
    success_url = reverse_lazy("user:user-list")

    def form_valid(self, form):
        user = form.save(commit=False)

        role = self.request.POST.get("role")  # Get the selected role from the request
        full_name = self.request.POST.get("full_name")
        if role:
            user.role = role

        if full_name:
            user.full_name = full_name

        user.save()

        # Redirect to success_url
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_role"] = User.USER_ROLE_CHOICES

        return context


class UserUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = User
    form_class = UserUpdateForm

    def form_valid(self, form):
        user = form.save(commit=False)

        # Set user"s role
        role = self.request.POST.get("role")
        full_name = self.request.POST.get("full_name")
        if role:
            user.role = role

        if full_name:
            user.full_name = full_name

        new_password = form.cleaned_data["new_password"]
        if new_password:
            user.set_password(new_password)
            # self.request.user = user
            update_session_auth_hash(self.request, user)

        user.save()

        return redirect(self.get_success_url())

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_role"] = User.USER_ROLE_CHOICES
        return context


class UserDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = User
    success_url = reverse_lazy("user:user-list")



class CustomPasswordChangeView(LoginRequiredMixin, View):
    template_name = "user/password_change.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        password = self.request.POST.get("new_pass")
        user = self.request.user
        user.force_password_change= False
        user.set_password(password)

        user.save()
        return redirect("zwroty:home")