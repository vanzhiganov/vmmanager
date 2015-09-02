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

from vmxml import DomainXML

from datetime import datetime

from domain import VM_STATE


class LibvirtDecorator(object):
    def __init__(self):
        self.netmanager = NetManager()
        self.imagemanager = ImageManager()

    def _connection(self, host):
        if not host:
            conn = libvirt.open("qemu:///system")
        else:
            conn = libvirt.open("qemu+ssh://%s/system" % host)
        return conn


    def define_validate(self, argv):
        print argv
        #set name
        if argv.has_key('name'):
            if type(argv['name']) != str:
                return False, 'vm name must be a string'
            if len(argv['name']) > VM_NAME_LEN_LIMIT:
                return False, 'vm name is too long'
        else:
            argv['name'] = argv['uuid']

        #mamory validation
        if argv.has_key('memory'):
            if type(argv['memory']) != int:
                return False, 'memory must be a integer' 
        else:
            return False, 'memory is needed'

        #cpu validation
        if argv.has_key('vcpu'):
            if type(argv['vcpu']) != int:
                return False, 'vcpu must be a integer'
        else:
            return False, 'vcpu is needed'

        return True, argv

    def define(self, group, image_snap, argv, local_net=True):
        #generate uuid
        argv['uuid'] = uuid.uuid4()

        #set diskname
        argv['diskname'] = argv['uuid']
        
        res, info = self.define_validate(argv)
        if res:
            argv = info
        else:
            return res, 'Argv error: %s' % info


        if type(group) != Group:
            group = Group.objects.filter(pk=group)
            if group:
                group = group[0]
        if type(group) != Group:
            return False, 'Group error'

        #host filter
        host = host_filter(group, argv['vcpu'], argv['memory'], local_net)
        if not host:
            return False, "Host filter: Host not find."

        vlan = self.netmanager.vlan_filter(host.vlan.all())
        if not vlan:
            return False, "Vlan filter: No available Vlan."
        argv['bridge'] = vlan.br

        
        #allocate mac address
        mac = self.netmanager.allocate_mac(vlan, argv['uuid'])
        if not mac:
            return False, 'Allocate mac error: %s' % self.netmanager.error
        argv['mac'] = mac
        
        #resource claim
        host.claim(argv['vcpu'], argv['memory'])

        # print xmldesc
        diskinfo = self.imagemanager.init_disk(image_snap, argv['diskname'])
        if not diskinfo:
            host.release(argv['vcpu'], argv['memory'])
            self.netmanager.release_mac(argv['mac'], argv['uuid'])
            return False, 'Disk init error: %s' % self.imagemanager.error

        argv.update(diskinfo)
        
        try:
            xml = DomainXML(argv['image'])
            xmldesc = xml.render(argv)
            # print xmldesc
            conn = self._connection(host.ipv4)
            vm = conn.defineXML(xmldesc)

            obj = Vm()
            obj.host    = host
            obj.image   = argv['image']
            obj.image_name = argv['image_name']
            obj.uuid    = str(argv['uuid'])
            obj.name    = str(argv['name'])
            obj.vcpu    = argv['vcpu']
            obj.mem     = argv['memory']
            obj.disk    = str(argv['diskname'])
            obj.deleted = False
            obj.save()
            
        except Exception,e:
            print e
            # release resource
            host.release(argv['vcpu'], argv['memory'])
            # release mac address
            self.netmanager.release_mac(argv['mac'], argv['uuid'])
            return False, 'Define error: %s' % e          
        return True, obj

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


    def create(self, group, image_snap, argv, creator, local_net=True):
        res,obj = self.define(group, image_snap, argv, local_net)
        if res:
            try:
                obj.creator = creator
                obj.save()
            except Exception, e:
                print e
                pass
            return self.start(obj)
        return False, obj
