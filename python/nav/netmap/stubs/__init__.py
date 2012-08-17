class Netbox(object):
    def __str__(self):
        return self.sysname
    def __unicode__(self):
        return u'%s' % self.sysname

    def __key(self):
        return (self.sysname)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

