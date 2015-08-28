import libvirt

class Connection(object):
    def __init__(self, host):
        if not host:
            self._conn = libvirt.open("qemu:///system")
        else:
            self._conn = libvirt.open("qemu+ssh://%s/system" % host)

    def __getattr__(self, name):
    	return getattr(self._conn, name)


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
        host = self._claim_resource(host, argv['vcpu'], argv['memory'])

        # print xmldesc
        diskinfo = self.imagemanager.init_disk(image_snap, argv['diskname'])
        if not diskinfo:
            host = self._release_resource(host, argv['vcpu'], argv['memory'])
            self.netmanager.release_mac(argv['mac'], argv['uuid'])
            return False, 'Disk init error: %s' % self.imagemanager.error

        argv.update(diskinfo)
        # print '111111111111111111', argv

        
        try:
            xmldesc = self._create_xml(argv)
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
            host = self._release_resource(host, argv['vcpu'], argv['memory'])
            # release mac address
            self.netmanager.release_mac(argv['mac'], argv['uuid'])
            return False, 'Define error: %s' % e
                


        return True, obj

    def _claim_resource(self, host, vcpu, memory):
        with transaction.atomic():
            h = Host.objects.select_for_update().get(pk=host.pk)
            h.cpu_allocated += vcpu
            h.mem_allocated += memory
            h.vm_created += 1
            h.save()
            return h

    def _release_resource(self, host, vcpu, memory):
        with transaction.atomic():
            h = Host.objects.select_for_update().get(pk=host.pk)
            h.cpu_allocated -= vcpu
            h.mem_allocated -= memory
            h.vm_created -= 1
            if h.cpu_allocated < 0:
                h.cpu_allocated = 0
            if h.mem_allocated < 0:
                h.mem_allocated = 0
            if h.vm_created < 0:
                h.vm_created = 0
            h.save()
            return h

    def create(self, group, image_snap, argv, creator, local_net=True):
        res,obj = self.define(group, image_snap, argv, local_net)
        # print res, obj, 222222222222222222
        if res:
            try:
                obj.creator = creator
                obj.save()
            except Exception, e:
                print e
                pass
            return self.start(obj)
            # vm = obj.get_domain()
            # if vm:
            #     print vm, 1111111111111111111111111
            #     return self.start(vm)
        return False, obj

    def _create_xml(self, argv):
        xml_tpl = self.imagemanager.get_xml_tpl(argv['image'])
        if xml_tpl == False:
            raise Exception('xml not find.')
        
        res = xml_tpl % argv
        print res
        return res