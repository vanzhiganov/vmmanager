from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from auth import staff_required

from compute.models import Center, Group, Host, Vm
from network.models import Vlan

from image.models import Ceph, Xml, Image

@login_required
@staff_required
def topo(request):
    dicts = {}
    centers = Center.objects.filter()
    dicts['centers'] = centers
    cephs = Ceph.objects.filter()
    dicts['cephs'] = cephs
    return render_to_response('vmadmin_topo.html',dicts,context_instance=RequestContext(request))	