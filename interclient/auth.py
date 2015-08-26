from django.http import HttpResponseRedirect
from django.contrib.auth.models import User 

def is_interclient_user(request):
    if hasattr(request.user, 'interclient_enable') and request.user.interclient_enable:
        return True
    return False

def interclient_user_required(func):
    def _is_interclient_user(request, *args, **argss):
        if is_interclient_user(request):
            return func(request, *args, **argss)
        return HttpResponseRedirect('/interclient/login/?next=/interclient/')
    return _is_interclient_user
