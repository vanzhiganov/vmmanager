"""vmmanager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin

from django.contrib.auth.views import login, logout

from site import interclientsite
urlpatterns = [

    url(r'^$', "vmmanager.views.index"),
    url(r'^admin/', include(admin.site.urls)),
    # url(r'^compute/', include('compute.urls')),
    #url(r'^network/', include('network.urls')),

    url(r'^vmadmin/', include('vmadmin.urls')),

    url(r'^interclient/', include('interclient.urls')),
    # url(r'^interclient/admin/', include(interclientsite.urls)),

    url(r'^oauth/', include('oauth.urls')),

    url(r'^accounts/login/$',  login, {'template_name':'login.html'}), 
    url(r'^accounts/logout/$', logout),
]

