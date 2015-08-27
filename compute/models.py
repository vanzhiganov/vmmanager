#coding=utf-8
from django.db import models
from uuid import UUID

from django.contrib.auth.models import User

from network.netmanager import NetManager

from network.models import Vlan

VM_NAME_LEN_LIMIT = 200

class Center(models.Model):
    name     = models.CharField('名称', max_length = 100, unique = True)
    location = models.CharField('位置', max_length = 100)
    desc     = models.CharField('简介', max_length = 200, null = True, blank = True)

    def __unicode__(self):
        return self.name

class Group(models.Model):
    center = models.ForeignKey(Center)
    name   = models.CharField(max_length = 100)
    desc   = models.CharField(max_length = 200, null = True, blank = True)
    admin_user = models.ManyToManyField(User, blank = True)

    def __unicode__(self):
        return self.name    

class Host(models.Model):
    group = models.ForeignKey(Group)
    vlan  = models.ManyToManyField(Vlan)
    ipv4  = models.GenericIPAddressField()
    cpu_total = models.IntegerField()
    cpu_allocated = models.IntegerField(default=0)
    mem_total = models.IntegerField()
    mem_allocated = models.IntegerField(default=0)
    mem_reserved = models.IntegerField(default=2097152) 
    vm_limit = models.IntegerField(default=10)
    vm_created = models.IntegerField(default=0)
    enable = models.BooleanField(default=True)
     
    def __unicode__(self):
        return self.ipv4


class Vm(models.Model):
    host = models.ForeignKey(Host)
    image = models.CharField(max_length=200)
    image_name = models.CharField(max_length=100)
    uuid = models.CharField(max_length=100)
    name = models.CharField(max_length=VM_NAME_LEN_LIMIT)
    vcpu = models.IntegerField()
    mem = models.IntegerField()
    disk = models.CharField(max_length=100)
    deleted = models.BooleanField()
    # task = models.CharField(max_length=50,null=True, blank=True)
    creator = models.CharField(max_length=200, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    def __unicode__(self):
        return self.name

    @property
    def status(self):
        from libvirt_decorator import VM_STATE
        domain = self.get_domain()
        if not domain:
            return 'not exist'
        try:
            info = domain.info()
            status = VM_STATE[info[0]]
        except Exception, e:
            status = 'error'
        return status
    
    @property
    def mac(self):
        return NetManager().get_mac_by_vmid(self.uuid)

    @property
    def ipv4(self):
        return NetManager().get_ipv4_by_vmid(self.uuid)

    @property
    def vlan(self):
        return NetManager().get_vlan_by_vmid(self.uuid)
    
    @property
    def br(self):
        return NetManager().get_br_by_vmid(self.uuid)

    def get_domain(self):
        from libvirt_decorator import LibvirtDecorator
        try:
            conn = LibvirtDecorator()._connection(self.host.ipv4)
        except Exception, e:
            print e
            return None
        try:
            if type(self.uuid) == UUID:
                return conn.lookupByUUID(self.uuid)
            else:
                return conn.lookupByUUIDString(self.uuid)
        except Exception, e:
            print e
            return None

    # @property
    # def image_name(self):
    #     image = Image.objects.filter(snap=self.image)
    #     if image:
    #         return image[0].name
    #     return ''

    @property
    def image_fullname(self):
        from image.models import Image
        image = Image.objects.filter(snap=self.image)
        if image:
            return image[0].fullname
        return ''

    @property
    def ceph_host(self):
        ceph = self.get_ceph()
        if ceph:
            return ceph.host
        return ''

    @property
    def ceph_pool(self):
        ceph = self.get_ceph()
        if ceph:
            return ceph.pool
        return ''

    def get_ceph(self):  
        from image.models import Image  
        image = Image.objects.filter(snap=self.image)
        if image:
            return image[0].ceph
        return None
    


class VmArchive(models.Model):
    center_id   = models.IntegerField(null=True, blank=True)
    center_name = models.CharField(max_length=100, null=True, blank=True)
    group_id    = models.IntegerField(null=True, blank=True)
    group_name  = models.CharField(max_length=100, null=True, blank=True)
    host_id     = models.IntegerField(null=True, blank=True)
    host_ipv4   = models.GenericIPAddressField(null=True, blank=True)
    ceph_host   = models.GenericIPAddressField(null=True, blank=True)
    name    = models.CharField(max_length=VM_NAME_LEN_LIMIT, null=True, blank=True)
    uuid    = models.CharField(max_length=100, null=True, blank=True)
    image   = models.CharField(max_length=200, null=True, blank=True)
    vcpu    = models.IntegerField(null=True, blank=True)
    mem     = models.IntegerField(null=True, blank=True)
    disk    = models.CharField(max_length=100, null=True, blank=True)
    mac     = models.CharField(max_length=17, null=True, blank=True)
    ipv4    = models.GenericIPAddressField(null=True, blank=True)
    vlan    = models.GenericIPAddressField(null=True, blank=True)
    br      = models.CharField(max_length=50, null=True, blank=True)

    archive_time = models.DateTimeField(auto_now_add=True)


    def archiveFromVm(self, vm):
        self.center_id      = vm.host.group.center.pk
        self.center_name    = vm.host.group.center.name
        self.group_id   = vm.host.group.pk
        self.group_name = vm.host.group.name
        self.host_id    = vm.host.pk
        self.host_ipv4  = vm.host.ipv4
        self.ceph_host  = vm.ceph_host
        self.name   = vm.name
        self.uuid   = vm.uuid
        self.image  = vm.image
        self.vcpu   = vm.vcpu
        self.mem    = vm.mem
        self.disk   = vm.ceph_pool + '/' + vm.disk
        self.mac    = vm.mac
        self.ipv4   = vm.ipv4
        self.vlan   = vm.vlan
        self.br     = vm.br
        try:
            self.save()
        except Exception, e:
            print "archive error:", e
            return False
        return True
