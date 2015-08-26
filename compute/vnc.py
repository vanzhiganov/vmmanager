#print os.system('ssh %s virsh vncdisplay %s'%(host.ipv4,argv['uuid']))
import os, uuid
import commands
from .models import Vm
from django.conf import settings

import thread

class TokenManager(object):
	class TManager(object):
		novnc_tokens = {}
		lock = thread.allocate_lock()
		def __init__(self):
			tokens_file = open(settings.TOKAN_FILE, 'r')
			for token in tokens_file.readlines():
				t = token.strip().split(':', 1)
				if len(t)<2:
					continue
				self.novnc_tokens[str(t[1].strip())] = str(t[0].strip())
			tokens_file.close()

		def add_token(self, vncid, hostip, port):
			self.lock.acquire()
			self.novnc_tokens['%s:%d' % (hostip, port)] = str(vncid)
			self.flush()
			self.lock.release()

		def del_token(self, vncid):
			self.lock.acquire()
			for k, v in self.novnc_tokens.items():
				if v == vncid:
					del self.novnc_tokens[k]
			# print self.novnc_tokens
			self.flush()
			self.lock.release()

		def flush(self):
			tokens_file = open(settings.TOKAN_FILE, 'w')
			for k, v in self.novnc_tokens.items():
				tokens_file.write('%s: %s\n' % (v, k))
			tokens_file.close()

	instance = TManager()


def set_vnc_token(vmid):
	obj = Vm.objects.filter(uuid = vmid)
	if obj:
		obj = obj[0]
	else:
		return False

	vm = obj.get_domain()
	if not vm:
		return False

	
	cmd = 'ssh %s virsh vncdisplay %s'%(obj.host.ipv4, obj.uuid)
	(res, info) = commands.getstatusoutput(cmd)
	if res == 0:
		try:
			port = settings.VNCSERVER_BASE_PORT + int(info.strip()[1:])
		except:
			return False
		vncid = uuid.uuid4()	
		instance = TokenManager().instance
		instance.add_token(vncid, obj.host.ipv4, port)
		return {
			'url':'http://%(host)s:%(port)d/vnc_auto.html?path=websockify/?token=%(vncid)s' % {
				'host': settings.NOVNC_HOST,
				'port': settings.NOVNC_PORT,
				'vncid': vncid
				},
			'id':vncid
			}
	return False

def del_vnc_token(vncid):
	
	vncid = str(vncid)
	instance = TokenManager().instance
	instance.del_token(vncid)
