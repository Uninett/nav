#
# Copyright (C) 2007-2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django import template
from django.utils.encoding import force_unicode

register = template.Library()


class UrlNode(template.Node):
    def __init__(self, params):
        self.get = template.Variable('request.GET')
        self.params = params

    def _get_GET(self, context):
        get = self.get.resolve(context).copy()
        for key, value in self.params:
            value = value.resolve(context)
            if key in get and not value:
                del get[key]
            elif value:
                get[key] = value
        return get

    def render(self, context):
        get = self._get_GET(context)
        return "?" + "&amp;".join([('%s=%s' % (k, get[k])) for k in get])


class InputNode(UrlNode):
    def render(self, context):
        get = self._get_GET(context)
        str = u'<input type="hidden" name="%s" value="%s" />'
        return u'\n'.join([str % (k, get[k]) for k in get])


def _get_url_params(token):
    raw_params = token.split_contents()
    tag_name = raw_params.pop(0)

    if len(raw_params) > 0 and len(raw_params) %2 != 0:
        error = "%r tag requires an even number of parameters" % tag_name
        raise template.TemplateSyntaxError, error

    params = []
    for index in xrange(0, len(raw_params), 2):
        params.append((raw_params[index],
                       template.Variable(raw_params[index + 1])))
    return params


@register.tag
def url_parameters(_parser, token):
    """Update and print URL GET parameters.

    Takes two and two parameters, the parameter to set/update and the value the
    parameter should be.

    An empty value will remove the specified parameter.

    Prints a GET url, ie: "?example=url&amp;url=parameterized"

    Examples:
        Print GET parameters:
        {% url_parameters %}

        Set filter param to 'name':
        {% url_parameters filter 'name' %}

        Also works with variables:
        {% url_parameters page my_page_value %}

        Set filter to 'name', page to my_page_value variable and remove sort:
        {% url_parameters filter 'name' page my_page_value sort '' %}
    """
    params = _get_url_params(token)
    return UrlNode(params)


@register.tag
def form_parameters(_parser, token):
    params = _get_url_params(token)
    return InputNode(params)
