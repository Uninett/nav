VERSION = (0, 1, 0)

__version__ = VERSION
__versionstr__ = '.'.join(map(str, VERSION))

# for now, propagate API
from hgdescribe.describe import *

