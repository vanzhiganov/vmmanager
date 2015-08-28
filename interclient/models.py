#coding=utf-8
from django.db import models

# Create your models here.
from django.conf import settings
from compute.models import Vm, Group
from network.models import Vlan
from image.models import Image
from django.contrib.auth.models import User 
from datetime import datetime
from message.models import Mail
class ICDUser(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    regist_time = models.DateTimeField(auto_now_add=True)
    confirm_time = models.DateTimeField(null=True, blank=True)
    uuid = models.CharField(max_length=100)
    user = models.OneToOneField(User, null=True, blank=True)

    def check_email(self):
        if self.email[-8:] == '@cnic.cn':
            return True
        return False

    def is_confirmed(self):
        if self.user == None:
            return False
        return True

    def send_confirm_email(self):
        mail = Mail()
        mail.receiver = self.email
        mail.subject = u'数据中心云主机平台账户注册-账户激活'
        from  django.template.loader  import  get_template 
        from django.template import Context
        t = get_template('interclient_regist_confirm.html')
        mail.content = t.render(Context({'domain':settings.DOMAIN, 'uuid':self.uuid, 'subject': mail.subject}))
        try:
            mail.save()
            mail.send()
            res = True
        except Exception, e:
            print e
            res = False

    def confirm(self):
        if not self.is_confirmed() and self.check_email() and not User.objects.filter(username=self.email).exists():
            obj = User()
            obj.username = self.email
            obj.interclient_enable = True
            obj.email = self.email
            obj.save()
            self.confirm_time = datetime.now()
            self.save()
            return True
        return False

class ICDVm(models.Model):
    user = models.ForeignKey(User)
    username = models.CharField(max_length=200)
    vmid     = models.CharField(max_length=100, unique=True)
    deleted  = models.BooleanField(default=False)
    cpu      = models.IntegerField()
    mem      = models.IntegerField()
    image    = models.CharField(max_length=200)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()


    @property
    def vm(self):
        vm = Vm.objects.filter(uuid=self.vmid)
        if vm:
            return vm[0]
        return None

class ICDTpl(models.Model):
    # group = models.ForeginKey(Group)
    cpu = models.IntegerField()
    mem = models.IntegerField()
    term = models.IntegerField(help_text='month')

    def __unicode__(self):
        return "%d vcpu | %dMB mem | %d month(s)" %(self.cpu, self.mem/1024, self.term)


class ICDConf(models.Model):
    group = models.ManyToManyField(Group)
    image = models.ManyToManyField(Image)
    tpl = models.ManyToManyField(ICDTpl)

class ICDSetting(models.Model):
    key = models.CharField(primary_key=True, max_length=100)
    value = models.CharField(max_length=200)
    desc = models.TextField(null=True, blank=True)

def get_setting(key):
    setting = ICDSetting.objects.filter(key = key)
    if setting:
        return setting[0].value
    return ''
