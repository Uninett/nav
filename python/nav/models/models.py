# Empty models.py tricks Django>=1.3? 1.4 system which are expecting
# to find models.py (module) from an app in INSTALLED_APPS.
#
# 'models' need to be listed as it expects to find model_name under
# app_label 'nav_models', hence we add this empty placeholder and add 'models' to
# INSTALLED_APPS to make sure 'nav_models.ModelName' is valid lookup on django
# form app_label.model_name

from .manage import *
from .api import *
from .arnold import *
from .cabling import *
from .event import *
from .logger import *
from .msgmaint import *
from .profiles import *
from .images import *
from .service import *
from .thresholds import *
