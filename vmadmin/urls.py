from django.conf.urls import include, url
from views import root, index
from topo import topo

urlpatterns = [
    url(r'^$', index),
    url(r'^topo/$', topo),
    url(r'^(?P<url>.+)', root),

]
