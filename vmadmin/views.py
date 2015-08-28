import uuid, json, libxml2
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect

from django.contrib.auth.decorators import login_required
from auth import staff_required

from compute.libvirt_decorator import *
from compute.models import Host, Center, Group, Vm
from image.models import Image
from network.models import Vlan
from utils.page import get_page

from compute.vnc import set_vnc_token, del_vnc_token
from compute.actions import VmAction

from utils.route import dispatch_url
from utils.views import AbsView

@login_required
@staff_required
def index(request):
    return HttpResponseRedirect('/vmadmin/vm/list/')

@login_required
@staff_required
def root(request, url):
    urlmap = {
        r'^vm/':VmView,
    }

    return dispatch_url(urlmap, url, request)

class VmView(AbsView):

    DefaultModel = Vm
    template_dir = 'vmadmin_'

    urlmap = {
        r'^$'           : ['index', ''],
        r'^create/$'    : ['create', 'create'],
        r'^list/$'      : ['list', 'list'],
        r'^detail/$'    : ['detail', 'detail'],
        r'^novnc/$'     : ['novnc', 'novnc'],

        r'^action/$'    : ['action', ''],
        r'^status/$'    : ['status', ''],
    }

    def index(self, request, template):
        return HttpResponseRedirect('/helpdesk/apply/query')


    def create(self, request, template):
        images = Image.objects.all()
        dicts = {}
        dicts['centers'] = self._get_centers(request)
        center_id = request.GET.get('center')
        center = self._get_center(request, center_id)

        # dicts['hosts'] = Host.objects.filter(group__admin_user=request.user)
        # dicts['images'] =  self._get_images(request)
        dicts['type_images'] = {}
        for image in self._get_images(request):
            if center and image.ceph.center != center:
                continue
            if dicts['type_images'].has_key(image.type):
                dicts['type_images'][image.type].append(image)
            else:
                dicts['type_images'][image.type] = [image]
        dicts['groups'] = {}
        for g in self._get_groups(request):
            if center and g.center != center:
                continue
            if dicts['groups'].has_key(g.center_id):
                dicts['groups'][g.center_id].append(g)
            else:
                dicts['groups'][g.center_id] = [g]
        # print dicts
        if request.method == "POST":
            centerid = request.POST.get('center')
            groupid = request.POST.get('group')
            image = request.POST.get('image')
            net = request.POST.get('net')
            if net == '0':
                is_local = False
            else:
                is_local = True
            cpu = request.POST.get('cpu')
            memory = request.POST.get('mem')
            num = request.POST.get('num')
            dicts['res'] = []
            for i in range(int(num)):
                res, obj = LibvirtDecorator().create( 
                    groupid, 
                    image, 
                    {
                        'memory':int(memory) * 1024,
                        'vcpu':int(cpu),
                    },
                    request.user.username,
                    is_local
                )
                # print res, obj
                if res == True:
                    dicts['res'].append((res, obj.host.ipv4, obj.ipv4))
                else:
                    dicts['res'].append((res, obj))
        return render_to_response(template,dicts,context_instance=RequestContext(request))

    def list(self, request, template):
        dicts = {}
        arg_center = request.GET.get('center')
        arg_group = request.GET.get('group')
        arg_host = request.GET.get('host')
        arg_ip = request.GET.get('ip')
        arg_creator = request.GET.get('creator')

        #querySet filter
        vms = self._get_vms(request).order_by('-create_time')
        if arg_center and Center.objects.filter(pk=arg_center).exists():
            vms = vms.filter(host__group__center_id = arg_center)
        if arg_group and Group.objects.filter(pk=arg_group).exists():
            vms = vms.filter(host__group_id = arg_group)
        if arg_host and Host.objects.filter(pk=arg_host).exists():
            vms = vms.filter(host_id = arg_host)
        if arg_creator:
            vms = vms.filter(creator__contains = arg_creator)

        #list filter
        if arg_ip:
            arg_ip = arg_ip.strip()
            vms = [vm for vm in vms if vm.ipv4[:len(arg_ip)] == arg_ip]

        dicts['p'] = get_page(vms, request)
        dicts['centers'] = self._get_centers(request)
        dicts['groups'] = [(str(g.pk), g.name) for g in self._get_groups(request)]
        dicts['hosts'] = [(str(h.pk), h.ipv4) for h in self._get_hosts(request).order_by('ipv4')]
        dicts['status_list'] = [(str(i[0]), i[1]) for i in VM_STATE.items()]
        return render_to_response(template, dicts, context_instance=RequestContext(request))


    def detail(self, request, template):
        vmid = request.GET.get('vmid')
        dicts = VmAction(vmid).get_detail()
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
            return HttpResponse(json.dumps({'res': True,'vmid': vmid, 'status': status}), content_type='application/json') 
        return HttpResponse(json.dumps({'res': False}), content_type='application/json') 

    def action(self, request, template):
        if request.method == 'POST':
            vmid   = request.POST.get('vmid')
            action = request.POST.get('action')
            vm = self._get_vm(request, vmid)
            if vm:
                actionobj = VmAction(vmid)
                res = actionobj.execute(action, request)
                if not res:
                    print 'Action error: %s' % actionobj.error
            else:
                res = False
        else:
            res = False
        return HttpResponse(json.dumps({'res': res}), content_type='application/json') 

    

    ####################### auth
    def _get_centers(self, request):
        return Center.objects.filter()

    def _get_center(self, request, centerid):
        cs = Center.objects.filter(pk = centerid)
        if cs:
            return cs[0]
        return None

    def _get_images(self, request):
        if request.user.is_superuser:
            return Image.objects.filter(enable = True).order_by('name')
        else:
            return Image.objects.filter(enable = True).order_by('name')

    def _get_vms(self, request):
        if request.user.is_superuser:
            return Vm.objects.all()
        else:
            return Vm.objects.filter(host__group__admin_user = request.user)

    def _get_vm(self, request, vmid):
        if request.user.is_superuser:
            vm = Vm.objects.filter(uuid = vmid)
        else:
            vm = Vm.objects.filter(host__group__admin_user = request.user, uuid = vmid)
        if vm:
            return vm[0]
        return None

    def _get_hosts(self, request):
        if request.user.is_superuser:
            return Host.objects.filter(enable = True)
        else:
            return Host.objects.filter(enable = True, group__admin_user = request.user)

    def _get_groups(self, request):
        if request.user.is_superuser:
            return Group.objects.all()
        else:
            return Group.objects.filter(admin_user = request.user)