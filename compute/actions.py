import libxml2
from models import Vm 
from libvirt_decorator import VM_STATE, LibvirtDecorator
from domain import Domain
class VmAction(object):
    def __init__(self, vmid):
        self.vmid = vmid
        vm = Vm.objects.filter(uuid = vmid)
        if vm:
            self.vmobj = vm[0]
            self.error = ''
        else:
            self.vmobj = None
            self.error = 'Vm (%s) not exist.' % vmid

    def get_detail(self):
        dicts = {}
        if self.vmobj:
            dicts['vmobj'] = self.vmobj
            vm = self.vmobj.get_domain()
            if vm != None:
                dicts['vminfo'] = {}
                info = vm.info()
                dicts['vminfo']['state'] = VM_STATE[info[0]]
                dicts['vminfo']['maxmem'] = info[1]
                dicts['vminfo']['usedmem'] = info[2]
                dicts['vminfo']['vcpus'] = info[3]
                def get_xml(ctx, path):
                    res = ctx.xpathEval(path)
                    if res is None or len(res) == 0:
                        value = ""
                    else:
                        value = res[0].content 
                    return value
                xmldesc = vm.XMLDesc(0)
                doc = libxml2.parseDoc(xmldesc)
                ctx = doc.xpathNewContext()

                dicts['vminfo']['type'] = get_xml(ctx, '/domain/os/type')
               
        return dicts

    def get_status(self, request=None):
        if self.vmobj:
            domain = self.vmobj.get_domain()
            if domain:  
                status = domain.status
            else:
                status = 'not exist'

        else:
            status = 'deleted'
        return status

    def execute(self, action, request=None):
        try:
            func = eval("self._vm_%s"%action)
        except Exception, e:
            return False, 'No such action.'

        try:
            after_status_func = eval('self._vm_%s_after_status' % action)
            after_status = after_status_func()
        except:
            after_status = None

        vm = Vm.objects.filter(uuid = self.vmid)
        info = {}
        if vm:
            vm = vm[0]
            domain = Domain(vm)
            
            res = func(domain)
            print res, after_status, vm.status
            if res and after_status and vm.status != after_status:
                res = False

            return res, self.error
        else:
            return False, 'Vmid error.'

    def _vm_shutdown(self, domain):
        if not domain:
            return True
            
        try:
            domain.shutdown()
            return True
        except Exception, e:
            self.error = e
            return False
    def _vm_shutdown_after_status(self):
        return 'shut off'

    def _vm_poweroff(self, domain):
        try:
            domain.destroy()
            return True
        except Exception,e:
            self.error = e
            return False
    def _vm_poweroff_after_status(self):
        return 'shut off'

    def _vm_start(self, domain):
        try:
            domain.create()
            return True
        except Exception, e:
            self.error = e 
            return False
    def _vm_start_after_status(self):
        return 'running'

    def _vm_reboot(self, domain):
        try:
            domain.reboot()
            return True
        except Exception, e:
            self.error = e 
            return False
    def _vm_reboot_after_status(self):
        return 'running'

    def _vm_delete(self, domain):
        return domain.delete()





