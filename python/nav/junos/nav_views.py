#
# Copyright (C) 2020 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""JunOS PyEZ tables/views for NAV specific use.

PyEZ' FactoryLoader is used to generate the desired Python classes from the
YAML-based definitions. These class definitions are dynamically inserted into this
module's namespace.

"""

from os.path import splitext
import yaml
from jnpr.junos.factory import FactoryLoader


def _loadyaml_bypass(yaml_file):
    """Bypass Juniper's loadyaml to utilize yaml.safe_load, thereby avoiding potential
    unintended code execution.
    """
    with open(yaml_file) as handle:
        return FactoryLoader().load(yaml.safe_load(handle.read()))


_YAML_ = splitext(__file__)[0] + ".yml"
globals().update(_loadyaml_bypass(_YAML_))
