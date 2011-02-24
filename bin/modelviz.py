#!/usr/bin/env python
# License retrived from:
# http://code.google.com/p/django-command-extensions/source/browse/trunk/LICENSE
#
# Copyright (c) 2007 Michael Trier
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Original file:
# http://code.google.com/p/django-command-extensions/source/browse/trunk/extensions/management/modelviz.py

"""Django model to DOT (Graphviz) converter
by Antonio Cavedoni <antonio@cavedoni.org>

This version has been modified to specifically work for Network
Administration Visualized.

Make sure your DJANGO_SETTINGS_MODULE is set to your project or
place this script in the same directory of the project and call
the script like this:

$ python modelviz.py [-h] [-d] [-g]  > <filename>.dot
$ dot <filename>.dot -Tpng -o <filename>.png

options:
    -h, --help
    show this help message and exit.

    -d, --disable_fields
    don't show the class member fields.

    -g, --group_models
    draw an enclosing box around models from the same app.
"""
__version__ = "0.9"
__svnid__ = "$Id$"
__license__ = "Python"
__author__ = "Antonio Cavedoni <http://cavedoni.com/>"
__contributors__ = [
   "Stefano J. Attardi <http://attardi.org/>",
   "limodou <http://www.donews.net/limodou/>",
   "Carlo C8E Miron",
   "Andre Campos <cahenan@gmail.com>",
   "Justin Findlay <jfindlay@gmail.com>",
   "Alexander Houben <alexander@houben.ch>",
   "Bas van Oostveen <v.oostveen@gmail.com>",
]

import getopt, sys

from django.core.management import setup_environ
from django.utils.encoding import mark_safe

try:
    import settings
except ImportError:
    pass
else:
    setup_environ(settings)

from django.template import Template, Context
from django.db import models
from django.db.models import get_models
from django.db.models.fields.related import \
    ForeignKey, OneToOneField, ManyToManyField

try:
    from django.db.models.fields.generic import GenericRelation
except ImportError:
    from django.contrib.contenttypes.generic import GenericRelation

head_template = """
digraph name {
  fontname = "Helvetica"
  fontsize = 12

  node [
    fontname = "Helvetica"
    fontsize = 12
    shape = "plaintext"
  ]
  edge [
    fontname = "Helvetica"
    fontsize = 12
  ]
  overlap = "20:compress"
  splines = "compound"
  nodesep = 0.8
  K = 0.5
  sep = 0.5

"""

body_template = """
{% if use_subgraph %}
subgraph {{ cluster_app_name }} {
  nodesep = 0.8
  K = 1
  sep = 1

  label=<
        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
        <TR><TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER"
        ><FONT FACE="Helvetica" COLOR="Black" POINT-SIZE="12"
        >{{ app_name }}</FONT></TD></TR>
        </TABLE>
        >
  color=olivedrab4
  style="rounded"
{% endif %}

  {% for model in models %}
    {{ model.app_name }}_{{ model.name }}[label=<
    <TABLE BGCOLOR="palegoldenrod" BORDER="0" CELLBORDER="0" CELLSPACING="0">
     <TR><TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER" BGCOLOR="olivedrab4"
     ><FONT FACE="Helvetica" COLOR="white" POINT-SIZE="24"
     >{{ model.name }}</FONT></TD></TR>

    {% if not disable_fields %}
        {% for field in model.fields %}
        <TR><TD ALIGN="LEFT" BORDER="0"
        ><FONT FACE="Helvetica" POINT-SIZE="24">{{ field.name }}{% if not field.blank %}*{% endif %}</FONT
        ></TD>
        <TD ALIGN="LEFT"
        ><FONT FACE="Helvetica" POINT-SIZE="24">{{ field.type }}</FONT
        ></TD></TR>
        {% endfor %}
    {% endif %}
    </TABLE>
    >]
  {% endfor %}

{% if use_subgraph %}
}
{% endif %}
"""

rel_template = """
  {% for model in models %}
    {% for relation in model.relations %}
    {% if relation.needs_node %}
    {{ relation.target }} [label=<
        <TABLE BGCOLOR="palegoldenrod" BORDER="0" CELLBORDER="0" CELLSPACING="0">
        <TR><TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER" BGCOLOR="olivedrab4"
        ><FONT FACE="Helvetica" COLOR="white" POINT-SIZE="24"
        >{{ relation.target }}</FONT></TD></TR>
        </TABLE>
        >]
    {% endif %}
    {{ model.app_name}}_{{ model.name }} -> {{ relation.target_app }}_{{ relation.target }}
    [label="{{ relation.name }}"] {{ relation.arrows }};
    {% endfor %}
  {% endfor %}
"""

tail_template = """
}
"""

def generate_dot(app_labels, **kwargs):
    disable_fields = kwargs.get('disable_fields', False)
    use_subgraph = kwargs.get('group_models', False)

    dot = head_template

    # Since where not using installed django apps in nav we have to load the
    # modules we are interested in manualy and make some changes to the code to
    # make this work.
    from nav.models import profiles, event, cabling, manage, msgmaint, oid, rrd, service

    apps=[profiles, event, cabling, manage, msgmaint, oid, rrd, service]

    graphs = []
    for app in apps:
        graph = Context({
            'name': '"%s"' % app.__name__,
            'app_name': "%s" % app.__name__.rsplit('.')[-1],
            'cluster_app_name': "cluster_%s" % app.__name__.replace(".", "_"),
            'disable_fields': disable_fields,
            'use_subgraph': use_subgraph,
            'models': []
        })

        for appmodel in get_models(app):
            if appmodel.__module__ != app.__name__:
                continue

            model = {
                'app_name': app.__name__.replace(".", "_"),
                'name': appmodel.__name__,
                'fields': [],
                'relations': []
            }

            # model attributes
            def add_attributes():
                model['fields'].append({
                    'name': field.name,
                    'type': type(field).__name__,
                    'blank': field.blank
                })

            for field in appmodel._meta.fields:
                add_attributes()

            if appmodel._meta.many_to_many:
                for field in appmodel._meta.many_to_many:
                    add_attributes()

            # relations
            def add_relation(extras=""):
                _rel = {
                    'target_app': field.rel.to.__module__.replace('.', '_'),
                    'target': field.rel.to.__name__,
                    'type': type(field).__name__,
                    'name': field.name,
                    'arrows': extras,
                    'needs_node': True
                }
                if _rel not in model['relations']:
                    model['relations'].append(_rel)

            for field in appmodel._meta.fields:
                if isinstance(field, ForeignKey):
                    add_relation()
                elif isinstance(field, OneToOneField):
                    add_relation('[arrowhead=none arrowtail=none]')

            if appmodel._meta.many_to_many:
                for field in appmodel._meta.many_to_many:
                    if isinstance(field, ManyToManyField):
                        add_relation('[arrowhead=normal arrowtail=normal]')
                    elif isinstance(field, GenericRelation):
                        add_relation(mark_safe('[style="dotted"] [arrowhead=normal arrowtail=normal]'))
            graph['models'].append(model)
        graphs.append(graph)

    nodes = []
    for graph in graphs:
        nodes.extend([e['name'] for e in graph['models']])


    for graph in graphs:
        # don't draw duplication nodes because of relations
        for model in graph['models']:
            for relation in model['relations']:
                if relation['target'] in nodes:
                    relation['needs_node'] = False
        # render templates
        t = Template(body_template)
        dot += '\n' + t.render(graph)

    for graph in graphs:
        t = Template(rel_template)
        dot += '\n' + t.render(graph)

    dot += '\n' + tail_template

    return dot

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdg",
                    ["help", "disable_fields", "group_models"])
    except getopt.GetoptError, error:
        print __doc__
        sys.exit(error)
    
    kwargs = {}
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print __doc__
            sys.exit()
        if opt in ("-d", "--disable_fields"):
            kwargs['disable_fields'] = True
        if opt in ("-g", "--group_models"):
            kwargs['group_models'] = True

    print generate_dot(args, **kwargs)

if __name__ == "__main__":
    main()
