#coding=utf-8
from django.db import models
from uuid import UUID

from django.db import transaction

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

    def claim_cpu(self, vcpu):
        with transaction.atomic():
            if self.cpu_allocated + vcpu > self.cpu_total:
                return False
            else:
                self.cpu_allocated += vcpu
                self.save()
                return True

    def release_cpu(self, vcpu):
        with transaction.atomic():
            self.cpu_allocated -= vcpu
            if self.cpu_allocated < 0:
                self.cpu_allocated = 0
            self.save()

    def claim_memory(self, memory):
        with transaction.atomic():
            if self.mem_allocated + memory + self.mem_reserved > self.mem_total:
                return False
            else:
                self.mem_allocated += memory
                self.save()
                return True

    def release_memory(self, memory):
        with transaction.atomic():
            self.mem_allocated -= memory
            if self.mem_allocated < 0:
                self.mem_allocated = 0
            self.save()

    def claim(self, vcpu, memory):
        with transaction.atomic():
            self.cpu_allocated += vcpu
            self.mem_allocated += memory
            self.vm_created += 1
            self.save()
    
    def release(self, vcpu, memory):
        with transaction.atomic():
            self.cpu_allocated -= vcpu
            self.mem_allocated -= memory
            self.vm_created -= 1
            if self.cpu_allocated < 0:
                self.cpu_allocated = 0
            if self.mem_allocated < 0:
                self.mem_allocated = 0
            if self.vm_created < 0:
                self.vm_created = 0
            self.save()

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
        domain = self.get_domain()
        if domain:
            return domain.status
        return 'not exist'
        
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
        from domain import Domain
        d = Domain(self)
        if d.exists():
            return d
        return None

    def show_mem(self):
        if self.mem < 1024:
            return '%d KB' % self.mem
        mem = self.mem / 1024.0
        if mem < 1024:
            return '%.2f MB' % mem
        mem = mem / 1024.0
        return '%.2f GB' % mem

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
    
    def update_cpu(self, vcpu):
        res = False
        if vcpu > self.vcpu:
            if self.host.claim_cpu(vcpu - self.vcpu):
                res = True
        else:
            self.host.release_cpu(self.vcpu - vcpu)
            res = True
        if res == True:
            self.vcpu = vcpu
            self.save()
        return res

    def update_memory(self, memory):
        res = False
        if memory > self.mem:
            if self.host.claim_memory(memory - self.mem):
                res = True
        else:
            self.host.release_memory(self.mem - memory)
            res = True
        if res == True:
            self.mem = memory
            self.save()
        return res

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
