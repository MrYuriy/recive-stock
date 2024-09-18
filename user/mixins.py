# myapp/mixins.py

from django.shortcuts import redirect
from django.urls import reverse

class CustomForcePasswordChangeMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.force_password_change:
            if request.path not in [reverse('password_change'), reverse('password_change_done')]:
                return redirect('user:password_change')
        return super().dispatch(request, *args, **kwargs)
