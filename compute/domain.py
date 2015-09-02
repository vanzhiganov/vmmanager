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
from vmxml import DomainXML, XMLEditor

from datetime import datetime


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
    def __init__(self, obj):
        self.netmanager = NetManager()
        self.imagemanager = ImageManager()
        self._obj = obj
        try:
            self._conn = libvirt.open("qemu+ssh://%s/system" % self._obj.host.ipv4) 
        except:
            self._conn = None
        else:
            try:
                self._vm = self._conn.lookupByUUIDString(self._obj.uuid)
            except:
                self._vm = None

    def __getattr__(self, name):
        if hasattr(self._obj, name):
            return getattr(self._obj, name)
        if self._vm:
            return getattr(self._vm, name)

    def delete(self):
        if self.exists():
            try:
                self.destroy()
            except:
                pass
            self.undefine()
            res = self.imagemanager.archive_disk(self._obj.get_ceph(), self._obj.uuid)
            print  'archive res:', res

        if not self._obj.get_domain():
            archive = VmArchive()
            if archive.archiveFromVm(self._obj):
                self.netmanager.release_mac(archive.mac, archive.uuid)
                self._obj.host.release(self._obj.vcpu, self._obj.mem)
                self._obj.delete()
                return True
        return False

    def exists(self):
        if self._vm:
            return True
        return False

    def _get_createxml_argv(self):
        ceph = self._obj.get_ceph()
        argv = {}
        argv['name'] = self._obj.name
        argv['uuid'] = self._obj.uuid
        argv['memory'] = self._obj.mem
        argv['vcpu'] = self._obj.vcpu
        argv['ceph_uuid'] = ceph.uuid
        argv['ceph_pool'] = ceph.pool
        argv['diskname'] = self._obj.disk
        argv['ceph_host'] = ceph.host
        argv['ceph_port'] = ceph.port
        argv['mac'] = self._obj.mac
        argv['bridge'] = self._obj.br
        return argv

    def set_cpu(self, cpu):
        try:
            cpu = int(cpu)
        except:
            return False

        if self.status == 'running':
            return False

        if cpu == self._obj.vcpu:
            return True
        org_cpu = self._obj.vcpu

        xml = XMLEditor()
        xml.set_xml(self.XMLDesc())
        root = xml.get_root()
        try:
            root.getElementsByTagName('vcpu')[0].firstChild.data = cpu
        except:
            return False

        xmldesc = root.toxml()
        if self._obj.update_cpu(cpu):
            try:
                print xmldesc
                res = self._conn.defineXML(xmldesc)
            except Exception, e:
                self._obj.update_cpu(org_cpu)
            else:
                return True
        return False

    def set_memory(self, memory):
        try:
            memory = int(memory)
        except:
            return False

        if self.status == 'running':
            return False

        if memory == self._obj.mem:
            return True
        org_memory = self._obj.mem

        xml = XMLEditor()
        xml.set_xml(self.XMLDesc())
        node = xml.get_node([ 'memory'])
        if node:
            node.firstChild.data = memory
        node1 = xml.get_node(['currentMemory'])
        if node1:
            node1.firstChild.data = memory
        xmldesc = xml.get_root().toxml()

        if self._obj.update_memory(memory):
            try:
                res = self._conn.defineXML(xmldesc)
            except Exception, e:
                print e
                self._obj.update_memory(org_memory)
            else:
                return True
        return False

    @property
    def status(self):
        if not self.exists():
            return 'not exist'
        try:
            info = self.info()
            status = VM_STATE[info[0]]
        except Exception, e:
            status = 'error'
        return status