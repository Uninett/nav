import string
class Service:
    def __init__(self, sysname, handler, args, id=''):
        self.sysname = sysname
        self.handler = handler
        self.args = args
        self.id = id
        self.active='t'
    def __cmp__(self, obj):
        return self.sysname==obj.sysname and self.handler==obj.handler and self.args==obj.args
    def __eq__(self, obj):
        return self.sysname==obj.sysname and self.handler==obj.handler and self.args==obj.args
    def __hash__(self):
        value = self.sysname.__hash__() + self.handler.__hash__() + self.args.__str__().__hash__()
        value = value % 2**31
        return int(value)
    def __repr__(self):
        strargs = string.join(map(lambda x: x+'='+self.args[x], self.args))
        return "%-20s %-10s %s" % (self.sysname, self.handler, strargs)
            
