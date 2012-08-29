class Netbox(object):
    def __str__(self):
        return str(self.sysname)

    def __unicode__(self):
        return u'%s' % self.sysname

    def __key(self):
        return (self.sysname)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def get_absolute_url(self):
        return None

class GwPortPrefix(object):
    def __str__(self):
        return str(self.gw_ip)

    def __unicode__(self):
        return u'%s' % self.gw_ip

    def __key(self):
        return (self.gw_ip)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

class Interface(object):
    def __str__(self):
        return str(self.iname, self.netbox)

    def __unicode__(self):
        return u'%s' % self.ifname, self.netbox

    def __key(self):
        return (self.ifname)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def get_absolute_url(self):
        return None


