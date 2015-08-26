from models import Center, Group, Host

import types
from random import randint

def host_filter(group, vcpu, memory, local_net):

    hosts = []
    for host in Host.objects.filter(group = group, enable=True, vlan__is_local=local_net):
        if host.vm_created < host.vm_limit and host.mem_allocated < host.mem_total - host.mem_reserved:
            hosts.append(host)
    print 'host filter debug:', hosts

    filter_strategy = HostFilterStrategy(host_filter_ram_strategy)
    filter_strategy.hosts   = hosts
    filter_strategy.vcpu    = vcpu
    filter_strategy.memory  = memory
    best_host = filter_strategy.execute()
    print 'best host:', best_host
    return best_host
 
class HostFilterStrategy(object):
    hosts = []
    vcpu = 0
    memory = 0
    def __init__(self, func=None):        
        if func is not None:
            self.execute = types.MethodType(func, self)      
        else:
            self.execute = types.MethodType('host_filter_random_strategy', self)

def host_filter_random_strategy(self):
    # print self.hosts
    if len(self.hosts) > 0:
        return self.hosts[randint(0, len(self.hosts)-1)]
    return None

# define better filter strategy in new functions, such as:
# def host_filter_ram_strategy(self):
#     ......
#     return Host object or None



def host_filter_ram_strategy(self):
    if len(self.hosts) == 0:
        return None
    max_ram = 0
    best = None
    for host in self.hosts:
        remain = host.mem_total - host.mem_allocated - host.mem_reserved
        if remain > max_ram:
            max_ram = remain
            best = host
    return best