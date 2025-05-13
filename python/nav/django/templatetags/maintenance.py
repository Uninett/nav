#
# Copyright (C) 2024 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Template tags for the maintenance tool"""

from django import template

from nav.web.maintenance.utils import MissingComponent

register = template.Library()


@register.filter
def model_verbose_name(model):
    """Returns the capitalized verbose name of a model"""
    if not model:
        return
    name = model._meta.verbose_name
    # Keep original capitalization, if any, otherwise apply our own
    # e.g. don't turn "IP Device" into "Ip device", but do turn "room" into "Room"
    return name if name[0].isupper() else name.capitalize()


@register.filter
def component_name(component):
    """Returns an identifying name of a model object used as a maintenance component"""
    if not component:
        return ""
    if hasattr(component, "sysname"):
        return component.sysname
    if hasattr(component, "handler"):
        return component.handler
    if isinstance(component, MissingComponent):
        return str(component)
    return component.pk


@register.filter
def component_description(component):
    """Returns a description of a component useful as a link title tooltip.  Returns
    an empty string if there is no further description than the component's name.
    """
    if isinstance(component, MissingComponent):
        return str(component)
    if hasattr(component, "ip"):
        return str(component.ip)
    return getattr(component, "description", "")


@register.filter
def component_db_table(component):
    """Returns the database table name of a model object used as a maintenance
    component.
    """
    if not component:
        return ""
    return component._meta.db_table
