class Netbox:
    def __init__(self, netboxid, deviceid, sysname, ip, up):
        self.netboxid = netboxid
        self.deviceid = deviceid
        self.sysname = sysname
        self.ip = ip
        self.up = up
    def __eq__(self, obj):
        if type(obj) == type(""):
            return self.ip == obj
        return self.netboxid == obj.netboxid
    def __repr__(self):
        return "%s (%s)" % (self.sysname, self.ip)
    def __str__(self):
        return "%s (%s)" % (self.sysname, self.ip)
    def __hash__(self):
        return self.ip.__hash__()
