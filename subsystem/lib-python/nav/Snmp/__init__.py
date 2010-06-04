import pysnmp

# Set default backend
backend = 'v2'
try:
    from pysnmp import version
    version.verifyVersionRequirement(3, 4, 3)
    backend = 'se'
except ImportError, e:
    pass

if backend == 'v2':
    from pysnmp_v2 import *
elif backend == 'se':
    from pysnmp_se import *
