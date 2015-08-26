#coding=utf-8
"""
child_proc = Process(target=_send_mail, args=('bob', 5))  
child_proc.start() 

"""
from django.db import models
from django.conf import settings
from django.core.mail import send_mail, EmailMessage

from multiprocessing import Process 

class Mail(models.Model):
    '''邮件'''
    creator = models.CharField(max_length=256, null=True)

    sender = models.CharField(max_length=256, null=True)
    receiver = models.CharField(max_length=256, null=False)
    subject = models.CharField(max_length=256, null=False)
    content = models.TextField(null=False)
    attach = models.TextField(null=True)

    mail_type = models.CharField(max_length=10, null=False, default="default")
    desc = models.TextField(null=True)
    add_time = models.DateTimeField(auto_now_add=True)

    def send(self, handler=None):
        if handler == None:
            handler = 'SYS'
        try:
            self.sender = settings.EMAIL_HOST_USER
            self.save()
            
            receiver = self.receiver.split(',')
            msg = EmailMessage(self.subject, self.content, self.sender, receiver)
            msg.content_subtype = "html"  # 主内体现在变成 text/html
            # msg.send()
            child_proc = Process(target=msg.send)  
            child_proc.start() 
            log = MailLog()
            log.mail  = self
            log.ser_name = settings.EMAIL_HOST
            log.ser_user = settings.EMAIL_HOST_USER
            log.handler = handler
            log.save()
        except:
            return False
        return True

    def safe_send(self, handler=None):
        if handler == None:
            handler = 'SYS'
       
        self.sender = settings.EMAIL_HOST_USER
        self.save()
        
        receiver = self.receiver.split(',')
        msg = EmailMessage(self.subject, self.content, self.sender, receiver)
        msg.content_subtype = "html"  # 主内体现在变成 text/html
        msg.send()
        log = MailLog()
        log.mail  = self
        log.ser_name = settings.EMAIL_HOST
        log.ser_user = settings.EMAIL_HOST_USER
        log.handler = handler
        log.save()
        
        return True

class MailLog(models.Model):
    '''邮件发送记录'''
    mail = models.ForeignKey(Mail,related_name='log')
    ser_name = models.CharField(max_length=256, null=True)  #发送服务器
    ser_user = models.CharField(max_length=256, null=True)  #发送账户
    handler = models.CharField(max_length=256, null=True)
    send_time = models.DateTimeField(auto_now_add=True)
