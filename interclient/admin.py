from django.contrib import admin
# from django.contrib.admin.sites import AdminSite

from models import ICDVm, ICDTpl, ICDConf, ICDSetting

# from vmmanager.site import interclientsite

interclientsite = admin.site

class ICDVmAdmin(admin.ModelAdmin):
    list_display = ('username', 'vmid', 'image', 'cpu', 'mem', 'start_time', 'end_time', 'deleted')
    list_filter = ['username', 'image', 'deleted']
interclientsite.register(ICDVm, ICDVmAdmin)


class ICDTplAdmin(admin.ModelAdmin):
    list_display = ('cpu', 'mem', 'term')
    # list_filter = ['username', 'image',]
interclientsite.register(ICDTpl, ICDTplAdmin)

class ICDConfAdmin(admin.ModelAdmin):
    filter_horizontal = ('group', 'image', 'tpl')
    # list_filter = ['username', 'image',]
interclientsite.register(ICDConf, ICDConfAdmin)

class ICDSettingAdmin(admin.ModelAdmin):
	list_display = ('key', 'value', 'desc')
interclientsite.register(ICDSetting, ICDSettingAdmin)