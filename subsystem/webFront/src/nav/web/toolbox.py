from nav import config
import os
import os.path

webfrontConfig = config.readConfig('webfront.conf')

def getToolList():
    """Searches the TOOLPATH search path for *.tool files and returns
    a list of Tool objects representing these files"""
    paths = {}
    if webfrontConfig.has_key('TOOLPATH'):
        paths = webfrontConfig['TOOLPATH'].split(os.pathsep)
    else:
        return None

    list = []
    for path in paths:
        if os.access(path, os.F_OK):
            filelist = os.listdir(path)
            for filename in filelist:
                if filename[-5:] == '.tool':
                    fullpath = os.path.join(path, filename)
                    list.append(Tool().load(fullpath))

    return list
    
class Tool:
    def __init__(self):
        self.name = ''
        self.uri = ''
        self.description = ''
        self.icon = ''

    def load(self, filename):
        if filename[0] != os.sep:
            filename = os.path.join(os.getcwd(), filename)
        dict = config.readConfig(filename)
        self.name        = dict['name']
        self.uri         = dict['uri']
        self.description = dict['description']
        self.icon        = dict['icon']
        
        return self
