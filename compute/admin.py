from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.db import transaction
from django.template.response import SimpleTemplateResponse, TemplateResponse


from django.contrib import admin
from .models import Center, Group, Host, Vm, VmArchive

csrf_protect_m = method_decorator(csrf_protect)


class CenterAdmin(admin.ModelAdmin):
    pass
admin.site.register(Center, CenterAdmin)

class GroupAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ('name','center','desc',)
    filter_horizontal = ('admin_user',)
    ordering = ('center', 'name')
admin.site.register(Group, GroupAdmin)

class HostAdmin(admin.ModelAdmin):
    list_display_links = ('ipv4',)
    list_display = ('ipv4','group', 'cpu_total','cpu_allocated','mem_total', 'mem_allocated',
    	'vm_limit', 'vm_created', 'enable')
    list_filter = ['group','enable']
    ordering = ('group', 'ipv4')
    filter_horizontal = ('vlan',)
admin.site.register(Host, HostAdmin)

class VmAdmin(admin.ModelAdmin):
    list_display = ('host', 'name', 'image', 'vcpu', 'mem', 'creator')
    list_filter = ['host', 'image',]
admin.site.register(Vm, VmAdmin)


class VmArchiveAdmin(admin.ModelAdmin):
    list_display = ('name', 'image', 'center_name', 'group_name', 'host_ipv4', 'ceph_host', 
    	'vcpu', 'mem', 'mac', 'ipv4', 'vlan', 'br', 'archive_time')
    list_filter = ['center_name', 'group_name', 'host_ipv4', 'ceph_host', 'image']
    ordering = ('archive_time', )
admin.site.register(VmArchive, VmArchiveAdmin)
