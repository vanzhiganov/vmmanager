import libvirt,os
import uuid
import commands
from models import Vm, Host, VmArchive, Group
from models import VM_NAME_LEN_LIMIT
from network.netmanager import NetManager
from image.imagemanager import ImageManager

from django.db import transaction
from random import randint
from host_filter import host_filter


from datetime import datetime

XML_TEMPLATE =  os.path.dirname(__file__) + '/default.xml'


VIR_DOMAIN_NOSTATE  =   0   #no state
VIR_DOMAIN_RUNNING  =   1   #the domain is running
VIR_DOMAIN_BLOCKED  =   2   #the domain is blocked on resource
VIR_DOMAIN_PAUSED   =   3   #the domain is paused by user
VIR_DOMAIN_SHUTDOWN =   4   #the domain is being shut down
VIR_DOMAIN_SHUTOFF  =   5   #the domain is shut off
VIR_DOMAIN_CRASHED  =   6   #the domain is crashed
VIR_DOMAIN_PMSUSPENDED =7   #the domain is suspended by guest power management
VIR_DOMAIN_LAST     =   8   #NB: this enum value will increase over time as new events are added to the libvirt API. It reflects the last state supported by this version of the libvirt API.

VM_STATE = {
    VIR_DOMAIN_NOSTATE:  'no state',
    VIR_DOMAIN_RUNNING: 'running',
    VIR_DOMAIN_BLOCKED: 'blocked',
    VIR_DOMAIN_PAUSED: 'paused',
    VIR_DOMAIN_SHUTDOWN: 'shut down',
    VIR_DOMAIN_SHUTOFF: 'shut off',
    VIR_DOMAIN_CRASHED: 'crashed',
    VIR_DOMAIN_PMSUSPENDED: 'suspended',
    VIR_DOMAIN_LAST: '',
}

class Domain(object):
    def __init__(self):
        self.netmanager = NetManager()
        self.imagemanager = ImageManager()


    def start(self, obj):
        try:
            #print os.system('ssh %s virsh vncdisplay %s'%(host.ipv4,argv['uuid']))\
            vm = obj.get_domain()
            if vm:
                vm.create()
            else:
                return False, 'vm not exist.'
        except Exception, e:
            return False, e
        return True, obj




    def delete(self, vmobj):
        vm = vmobj.get_domain()
        if vm:
            try:
                vm.destroy()
            except:
                pass
            vm.undefine()
            res = self.imagemanager.archive_disk(vmobj.get_ceph(), vmobj.uuid)
            print  'archive res:', res
        if not vmobj.get_domain():
            archive = VmArchive()
            if archive.archiveFromVm(vmobj):
                self.netmanager.release_mac(archive.mac, archive.uuid)
                self._release_resource(vmobj.host, vmobj.vcpu, vmobj.mem)
                vmobj.delete()
                return True
        return False

