#coding=utf-8
from dateutil.relativedelta import relativedelta
from datetime import datetime
import json
from django.shortcuts import render, render_to_response

from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse

# from oauth import login_required
from django.contrib.auth.decorators import login_required
from auth import interclient_user_required

from models import ICDConf, ICDTpl, ICDVm, get_setting, ICDUser

from compute.libvirt_decorator import LibvirtDecorator
from compute.models import Center, Group, Vm
from image.models import Image
from compute.actions import VmAction
from utils.route import dispatch_url
from utils.views import AbsView

from compute.vnc import set_vnc_token, del_vnc_token
from django.views.decorators.http import require_http_methods
from random import choice
import string
from django.core.cache import cache
from message.models import Mail
import uuid
from django.contrib.auth.models import User 

@interclient_user_required
@login_required
def index(request):
    if request.user.interclient_enable:
        return HttpResponseRedirect('/interclient/vm/list/')
    return HttpResponseRedirect('/interclient/login/')

# @require_http_methods(['GET', 'POST'])
def register(request):
    info = ''
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        res = True
        if not name or not email:
            res = False 
            info = '注册失败，请正确填写表单。'
        obj = ICDUser()
        obj.email = email
        obj.name = name
        if obj.check_email():
            exist = ICDUser.objects.filter(email = obj.email)
            if exist.filter(user__isnull = False).exists():
                res = False
                info = '用户已存在。'
            else:
                valid_date = datetime.now() + relativedelta(days = -7)
                # print valid_date
                exist = exist.filter(regist_time__gt = valid_date)
                if exist:
                    exist[0].send_confirm_email()
                    res = False
                    info = '您已经注册,请登录邮箱进行验证,并设置密码'
                else:
                    obj.uuid = uuid.uuid4()
                    obj.confirm_time = None
                    obj.user = None
                    obj.save()
                    obj.send_confirm_email()
                    info = '请登录邮箱进行验证，并设置密码'
        else:
            info = '仅对 @cnic.cn 邮箱开放注册。'
        return HttpResponse(json.dumps({'res':res,'info':info}), content_type='application/json')
    else:
        return render_to_response('interclient_register.html', {'info': info}, context_instance=RequestContext(request))        
  

def confirm(request):
    user = None
    res  = True
    error = ''
    if request.method == "POST":
        uid = request.POST.get('uuid')
        passwd = request.POST.get('passwd')
        passwd2 = request.POST.get('passwd2')

        obj = ICDUser.objects.filter(uuid = uid)
        if obj:
            user = obj[0]
            if user.is_confirmed():
                res = False
                error = '不能重复激活，请使用首次激活时设置的密码登录。'
        else:
            res = False
            error = 'UUID ERROR.'
        if res and len(passwd) < 6:
            res = False
            error = '密码长度不能小于6位。'
        if res and passwd != passwd2:
            res = False
            error = '两次输入密码不一致。'
        if res:
            uobj = User()
            uobj.username = user.email
            uobj.email = user.email
            uobj.interclient_enable = True
            uobj.realname = user.name
            uobj.set_password(passwd)
            uobj.save()
            user.user = uobj
            user.confirm_time = datetime.now()
            user.save()
            return HttpResponseRedirect('/interclient/')
        
    else:
        uid = request.GET.get('uuid')
        user = None
        if uid:
            obj = ICDUser.objects.filter(uuid = uid)
            if obj:
                user = obj[0]
                if user.is_confirmed():
                    return HttpResponseRedirect('/interclient/')
                
    return render_to_response('interclient_confirm.html', {'user': user, 'res': res, 'error': error}, context_instance=RequestContext(request))

@interclient_user_required
@login_required
def root(request, url):
    urlmap = {
        r'^vm/':ICDVmView,
    }
    return dispatch_url(urlmap, url, request)

class ICDVmView(AbsView):

    DefaultModel = ICDVm
    template_dir = 'interclient_'

    urlmap = {
        r'^/$'           : ['index', ''],
        r'^create/$'    : ['create', 'create'],
        r'^list/$'      : ['list', 'list'],
        r'^detail/$'    : ['detail', 'detail'],
        r'^novnc/$'     : ['novnc', ''],

        r'^action/$'    : ['action', ''],
        r'^status/$'    : ['status', ''],
    }

    def index(self, request, template):
        return HttpResponseRedirect('/interclient/vm/list/')
       
    def list(self, request, template):
      dic = {}
      dic['vms'] = ICDVm.objects.filter(user=request.user, deleted=False)
      return render_to_response(template, dic, context_instance=RequestContext(request))

    def _can_create(self, user):
        vm_num = ICDVm.objects.filter(user = user, deleted=False).count()
        vm_num_limit = get_setting('vm_num_limit')

        if vm_num_limit.isdigit():
            vm_num_limit = int(vm_num_limit)
        else:
            vm_num_limit = 3

        return vm_num < vm_num_limit

    def create(self, request, template):
        dic = {}
        # dic['user_name'] = request.session.get('user_name', False)
        if self._can_create(request.user):
            if request.method == 'POST':
                group = request.POST.get('group')
                image = request.POST.get('image')
                tpl = request.POST.get('tpl')
                try:
                    group = Group.objects.get(pk=group)
                    tpl = ICDTpl.objects.get(pk=tpl)
                except Exception, e:
                    print e
                    group = False
                    tpl = False
                if image and group and tpl:
                    res, vm = LibvirtDecorator().create(
                        group,
                        image,
                        {
                            'memory': int(tpl.mem),
                            'vcpu': int(tpl.cpu)
                        },
                        'interclient_' + request.user.username,
                        True
                        )
                    if res == True:
                        now = datetime.now()
                        obj = ICDVm()
                        obj.user = request.user
                        obj.username = request.user.username
                        obj.vmid = vm.uuid
                        obj.cpu = tpl.cpu
                        obj.mem = tpl.mem
                        obj.image = vm.image_fullname
                        obj.start_time = now
                        obj.end_time = now + relativedelta(months=tpl.term)
                        obj.save()
                        return HttpResponseRedirect('/interclient/vm/list/')
                    else:
                        dic['error'] = vm
                else:
                    dic['error'] = 'create error: group or image or config error.'
            conf = ICDConf.objects.all()
            if conf:
                conf = conf[0]
                dic['groups'] = conf.group.all()
                dic['images'] = conf.image.filter(enable=True)
                dic['type_images'] = {}
                for image in dic['images']:
                    if dic['type_images'].has_key(image.type):
                        dic['type_images'][image.type].append(image)
                    else:
                        dic['type_images'][image.type] = [image]
                dic['tpls'] = conf.tpl.all()
        else:
            dic['cant_create'] = True
            dic['error'] = '云主机数量达到上限，您不能再创建新的云主机。'
        return render_to_response(template, dic, context_instance=RequestContext(request))


    def detail(self, request, template):
        dicts = {}
        vmid = request.GET.get('vmid')
        vmobj = self._get_vm(request, vmid)
        dicts.update(VmAction(vmid).get_detail())
        return render_to_response(template, dicts, context_instance=RequestContext(request))

    def novnc(self, request, template):
        vncid = request.GET.get("vncid")
        if vncid:
            del_vnc_token(vncid)
            return HttpResponse('<script language="javascript">window.close();</script>')
        else:
            
            vmid = request.GET.get('vmid')
            obj = self._get_vm(request, vmid)

            if obj:
                info = set_vnc_token(vmid)
                if info:
                    # return HttpResponseRedirect(url)
                    return render_to_response('novnc.html', info, context_instance=RequestContext(request))
            return HttpResponse('vnc not available.')


    def status(self, request, template):
        if request.method == 'POST':
            vmid = request.POST.get('vmid')
            status = VmAction(vmid).get_status(request)
            # print status, 66666666666666
            if status == 'deleted' and ICDVm.objects.filter(vmid = vmid, deleted=False).exists():
                status = 'vm deleted'
            return HttpResponse(json.dumps({'res': True,'vmid': vmid, 'status': status}), content_type='application/json') 
        return HttpResponse(json.dumps({'res': False}), content_type='application/json') 

    def action(self, request, template):
        if request.method == 'POST':
            vmid   = request.POST.get('vmid')
            action = request.POST.get('action')
            obj = self._get_vm(request, vmid)
            if obj:
                actionobj = VmAction(vmid)
                res = actionobj.execute(action, request)
                if res:
                    if action == 'delete':
                        obj.deleted = True
                        obj.save()
                else:
                    print actionobj.error
            else:
                print 'vmid error.'
                res = False
        else:
            res = False
        return HttpResponse(json.dumps({'res': res}), content_type='application/json') 

    

    ####################### auth
    def _get_centers(self, request):
        return Center.objects.filter()

    def _get_images(self, request):
        conf = ICDConf.objects.filter()
        if not conf:
            return Image.objects.none()
        return conf[0].image.filter(enable = True)

    def _get_vms(self, request):
        return ICDVm.objects.filter(user=request.user, deleted=False)

    def _get_vm(self, request, vmid):
        vm = ICDVm.objects.filter(user = request.user, vmid = vmid, deleted=False)
        if not vm:
            return None 
        return vm[0]


