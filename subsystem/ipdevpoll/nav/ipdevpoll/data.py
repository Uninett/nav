

class _MetaData(type):
    def __init__(cls, name, bases, dict):
        super(_MetaData, cls).__init__(name, bases, dict)
        cls.all = []

class _Data(object):
    __metaclass__ = _MetaData

    fields = []
    bad_serials = ["0", "0x0E", "0x12", "1234"]

    def __init__(self, **kwargs):
        for field in self.fields:
            setattr(self, field, kwargs.pop(field, None))

        if kwargs:
            raise Exception()

        self.__class__.all.append(self)

    @classmethod
    def clear(self):
        self.all = []

    @classmethod
    def save(self):
        pass

class Device(_Data):
    fields = ['id', 'serial', 'sw_ver', 'fw_ver', 'hw_ver']

class Netbox(_Data):
    fields = Device.fields + ['sysname', 'upsince', 'uptime', 'vlans', 'device_id']

class Module(_Data):
    fields = Device.fields + ['number', 'model', 'description', 'device_id']

class Interface(_Data):
    # FIXME list is _far_ from complete
    fields = ['id', 'ifname', 'netbox_id']

class Prefix(_Data):
    # FIXME not sure if this is right
    fields = ['addr', 'hrsp', 'prefix', 'vlan']

class Vlan(_Data):
    fields = ['id', 'vlan', 'description', 'net_type_id', 'org_id', 'usage_id']

class Arp(_Data):
    pass

class Memory(_Data):
    pass
