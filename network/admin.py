from django.contrib import admin

# Register your models here.

from models import Vlan, MacIP

class VlanAdmin(admin.ModelAdmin):
    list_display = ('vlan', 'br', 'enable',)
    # list_filter = ['host', 'image',]
admin.site.register(Vlan, VlanAdmin)


class MacIPAdmin(admin.ModelAdmin):
    list_display = ('vlan', 'mac', 'ipv4', 'vmid', 'enable')
    # list_filter = ['vlan', 'ipv4',]
admin.site.register(MacIP, MacIPAdmin)
