from django.db import transaction
from models import Vlan, MacIP

from random import randint
class NetManager(object):
    error = ''
    def allocate_mac(self, vlan, vmid):
        if type(vlan) != Vlan:
            vlan = Vlan.objects.filter(pk = vlan)
            if not vlan:
                self.error =  'vlan error'
                return None
            vlan = vlan[0]

        mac = MacIP.objects.filter(vlan = vlan, vmid = vmid, enable=True)
        if mac:
            return mac[0]
            
        with transaction.atomic():
            mac = MacIP.objects.select_for_update().filter(vlan = vlan, vmid='', enable=True)
            if mac:
                mac = mac[0]
                mac.vmid = vmid
                mac.save()
            else:
                self.error = 'no valid mac'
                return None
        return mac.mac

    def release_mac(self, mac, vmid):
        print 'release mac:', mac, vmid 
        macipobj = MacIP.objects.filter(mac=mac, vmid=vmid, enable=True)
        for m in macipobj:
            print 'set null', m.mac
            m.vmid = ''
            m.save()

    def get_mac_by_vmid(self, vmid):
        macip = MacIP.objects.filter(vmid = vmid)
        if macip:
            return macip[0].mac
        return ''

    def get_ipv4_by_vmid(self, vmid):
        macip = MacIP.objects.filter(vmid = vmid)
        if macip:
            return macip[0].ipv4
        return ''

    def get_vlan_by_vmid(self, vmid):
        macip = MacIP.objects.filter(vmid = vmid)
        if macip:
            return macip[0].vlan.vlan
        return ''

    def get_br_by_vmid(self, vmid):
        macip = MacIP.objects.filter(vmid = vmid)
        if macip:
            return macip[0].vlan.br 
        return  ''

    def vlan_filter(self, vlans):
        v = []
        for vlan in vlans:
            if vlan.enable:
                v.append(vlan)
        if len(v) > 0:
            return v[randint(0,len(v)-1)]
        return None