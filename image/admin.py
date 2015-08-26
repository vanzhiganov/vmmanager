from django.contrib import admin

from models import Ceph, Image, Xml

class CephAdmin(admin.ModelAdmin):
    list_display_links = ('host',)
    list_display = ('host', 'pool', 'port', 'uuid')
    ordering = ('host',)

admin.site.register(Ceph, CephAdmin)


class ImageAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ('ceph', 'name', 'version', 'snap', 'desc', 'xml', 'enable', 'type')
    list_filter = ['ceph', 'name', 'enable', 'type']
    search_fields = ['version', 'snap', 'desc']
    ordering = ('ceph', 'name', 'version')
admin.site.register(Image, ImageAdmin)

class XmlAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ('name', 'desc')
    # ordering = ('ceph', 'name', 'version')
admin.site.register(Xml, XmlAdmin)
