from django.db import models

class Vlan(models.Model):
    vlan = models.GenericIPAddressField()
    br = models.CharField(max_length=50)
    is_local = models.BooleanField(default=True)
    enable = models.BooleanField()

    def __unicode__(self):
    	return self.vlan

class MacIP(models.Model):
    vlan = models.ForeignKey(Vlan)
    mac = models.CharField(max_length=17)
    ipv4 = models.GenericIPAddressField()
    vmid = models.CharField(max_length=100,null=True,blank=True, default='')
    enable = models.BooleanField(default=True)

    def __unicode__(self):
    	return self.mac

