 
from django.conf.urls import include, url
from django.contrib import admin
# from views import vm_create, vm_list, vm_novnc, vm_action, vm_status, vm_detail
from views import root, index
from topo import topo
urlpatterns = [
    url(r'^$', index),

    url(r'^topo/$', topo),
    # url(r'^list/', vm_list),
    # url(r'^action/', vm_action),
    # url(r'^status/', vm_status),
    # url(r'^detail/', vm_detail),

    # url(r'^novnc/', vm_novnc),


    url(r'^(?P<url>.+)', root),

]
