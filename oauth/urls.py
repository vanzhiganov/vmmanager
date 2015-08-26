from django.conf.urls import patterns, include
from django.conf import settings

urlpatterns = patterns('oauth.views',
    (r'login/', 'login'),
    (r'logout/', 'logout'),
    (r'callback/', 'callback'),
)