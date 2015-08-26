import commands

def ceph_clone(ceph_host, src, dst):
    cmd = 'ssh %(ceph_host)s rbd clone %(src)s %(dst)s' % {'ceph_host':ceph_host, 'src':src, 'dst':dst}
    print cmd
    return commands.getstatusoutput(cmd)


def ceph_mv(ceph_host, src, dst):
    cmd = 'ssh %(ceph_host)s rbd mv %(src)s %(dst)s' % {'ceph_host':ceph_host, 'src':src, 'dst':dst}
    print cmd
    return commands.getstatusoutput(cmd)
