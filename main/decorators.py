from django.shortcuts import redirect
from django.contrib.auth.models import Group


def admin_required(view_func):

    def wrapper_func(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('/accounts/login/')

        if request.user.groups.filter(name='admin_owner').exists():
            return view_func(request, *args, **kwargs)

        return redirect('/')

    return wrapper_func