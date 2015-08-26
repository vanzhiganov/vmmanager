from models import Image, Ceph
from random import randint
from datetime import datetime

class ImageManager(object):
    error = ''

    def init_disk(self, image_snap, diskname):
        image = Image.objects.filter(snap = image_snap)
        if not image:
            self.error = 'Image (%s) not exist.' % image_snap
            return False

        image = image[0]
        res , info = image.ceph.clone(image.snap, str(diskname))
        if res == 0:
            return {
                'image': image.snap,
                'image_name': image.fullname,
                'ceph_host': image.ceph.host,
                'ceph_port': image.ceph.port,
                'ceph_uuid': image.ceph.uuid,
                'ceph_pool': image.ceph.pool
            }
        else:
            self.error = info
            res = False
        
    def archive_disk(self, ceph, disk_name):
        if type(ceph) != Ceph:
            ceph = Ceph.objects.filter(pk = ceph)
            if ceph:
                ceph = ceph[0]
        if type(ceph) != Ceph:
            return False

        print 'archive disk'
        res, info = ceph.mv(disk_name, 'del_'+str(disk_name)+'_'+datetime.now().strftime("%Y%m%d%H%M%S%f"))
        if res == 0:
            res = True
        else:
            self.error = info
            res = False
        return res

    def get_xml_tpl(self,image_snap):
        image = Image.objects.filter(snap = image_snap)
        if not image:
            self.error = 'Image (%s) not exist.' % image_snap
            return False
        image = image[0]
        return image.xml.xml