"""
 @author bobfu
 @date 2014-02-28
"""
from django.http import HttpResponseRedirect
from django.conf import settings

def is_login(request):
    if request.session.has_key('user_name') and request.session.has_key('access_token') and request.session.has_key('refresh_token'):
        return True
    return False

def login_required(func):
    def _is_login(request, *args, **argss):
        if is_login(request):
            return func(request, *args, **argss)
        return HttpResponseRedirect('/oauth/login?next_url=' + request.path_info)
    return _is_login

def admin_required(func):
    def _is_admin(request, *args, **argss):
        if is_login(request) and request.session['user_name'] in settings.ADMIN_LIST:
            return func(request, *args, **argss)
        return HttpResponseRedirect('/oauth/login')
    return _is_admin
