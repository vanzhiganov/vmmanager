#coding=utf-8
from django.db import models
import commands
from compute.models import Center

class Ceph(models.Model):
    center = models.ForeignKey(Center)
    host = models.GenericIPAddressField()
    port = models.IntegerField(default=6789)
    uuid = models.CharField(max_length=100)
    pool = models.CharField(max_length=100)

    def __unicode__(self):
        return self.host + '_' + self.pool


    class Meta:
        verbose_name = 'CephPool '
        verbose_name_plural = 'CephPools'
        unique_together = ('host', 'pool')


    def clone(self, src, dst):
        cmd = 'ssh %(ceph_host)s rbd clone %(ceph_pool)s/%(src)s %(ceph_pool)s/%(dst)s' % {
            'ceph_host':self.host, 
            'ceph_pool':self.pool,
            'src':src, 
            'dst':dst
        }
        print cmd
        return commands.getstatusoutput(cmd)

    def mv(self, src, dst):
        cmd = 'ssh %(ceph_host)s rbd mv %(ceph_pool)s/%(src)s %(ceph_pool)s/%(dst)s' % {
            'ceph_host':self.host, 
            'ceph_pool':self.pool,
            'src':src, 
            'dst':dst
        }
        print cmd
        return commands.getstatusoutput(cmd)

    def rm(self, dst):
        cmd = 'ssh %(ceph_host)s rbd rm %(ceph_pool)s/%(dst)s' % {
            'ceph_host':self.host, 
            'ceph_pool':self.pool,
            'dst':dst
        }
        print cmd
        return commands.getstatusoutput(cmd)


class Xml(models.Model):
    name = models.CharField(max_length=100, unique=True)
    xml = models.TextField()
    desc = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name 

class Image(models.Model):
    ceph = models.ForeignKey(Ceph)
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=100)
    snap  = models.CharField(max_length=200, unique=True)
    desc = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now = True)
    enable = models.BooleanField(default=True)
    xml = models.ForeignKey(Xml)
    type = models.CharField(max_length=100, default='基础镜像')

    def __unicode__(self):
        return self.snap

    class Meta:
        unique_together = ('ceph', 'name', 'version')

    @property
    def fullname(self):
        return '%s %s' % (self.name, self.version)
    



