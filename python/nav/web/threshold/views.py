#
# Copyright 2011 Uninett AS
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
"""Controllers for threshold app"""

import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from nav.metrics.names import raw_metric_query
from nav.metrics.graphs import get_simple_graph_url, Graph
from nav.models.thresholds import ThresholdRule
from nav.web.modals import render_modal
from nav.web.threshold.forms import ThresholdForm
from nav.web.auth.utils import get_account
from nav.web.utils import create_title


TITLE = 'Thresholds'


def get_path():
    """Get default navpath for this app"""
    return [('Home', '/'), (TITLE, reverse('threshold-index'))]


def index(request):
    """Base controller"""

    rules = ThresholdRule.objects.all().order_by('id')
    context = {'title': TITLE, 'navpath': get_path(), 'rules': rules}
    return render(request, 'threshold/base.html', context)


def add_threshold(request, metric=None):
    """Controller for threshold search"""

    if request.method == 'POST':
        form = ThresholdForm(request.POST)
        metric = request.POST.get('target')
        if form.is_valid():
            handle_threshold_form(form, request)
            return redirect('threshold-index')
    else:
        if metric:
            form = ThresholdForm(initial={'target': metric})
        else:
            form = ThresholdForm()

    heading = 'Add threshold rule'
    navpath = get_path() + [(heading,)]
    title = create_title(navpath)
    context = {
        'heading': heading,
        'form': form,
        'metric': metric,
        'title': title,
        'navpath': navpath,
        'id': None,
    }

    return render(request, 'threshold/set_threshold.html', context)


def edit_threshold(request, rule_id):
    """Controller for editing threshold rules"""

    rule = get_object_or_404(ThresholdRule, pk=rule_id)

    if request.method == 'POST':
        form = ThresholdForm(request.POST, instance=rule)
        metric = request.POST.get('target')
        if form.is_valid():
            handle_threshold_form(form, request)
            return redirect('threshold-index')
    else:
        form = ThresholdForm(instance=rule)
        metric = rule.target

    heading = 'Edit threshold rule'
    navpath = get_path() + [(heading,)]
    title = create_title(navpath)
    context = {
        'heading': heading,
        'form': form,
        'metric': metric,
        'title': title,
        'navpath': navpath,
        'id': rule.id,
    }
    return render(request, 'threshold/set_threshold.html', context)


def delete_threshold(request, rule_id):
    """Controller for deleting threshold rules"""
    if request.method == 'POST':
        rule = get_object_or_404(ThresholdRule, pk=rule_id)
        rule.delete()

    return redirect('threshold-index')


def handle_threshold_form(form, request):
    """Create threshold based on form data

    :param ThresholdForm form: A user defined threshold
    :param HttpRequest request: The request object
    """
    threshold = form.save(commit=False)
    threshold.created = datetime.datetime.now()
    threshold.creator = get_account(request)
    threshold.save()


def threshold_help_modal(request):
    """
    Render a modal with help information for adding threshold rules
    """
    return render_modal(
        request,
        'threshold/_threshold_help_modal.html',
        modal_id='threshold-help-modal',
        size="large",
    )


def threshold_search(request):
    """Returns json formatted searchresult"""
    result = []
    if 'term' in request.GET:
        term = enhance_term(request.GET['term'])
        metrics = get_metrics(term)
        for metric in metrics:
            result.append(
                {
                    'label': metric['id'],
                    'value': metric['id'],
                    'expandable': metric['expandable'],
                }
            )

    return JsonResponse({"items": result})


def enhance_term(term):
    """Format the term based on certain rules

    :type term: str
    """
    if term.endswith('.'):
        term += '*'

    return term


def get_metrics(term):
    """Get metrics based on search term

    :type term: str
    """
    metrics = raw_metric_query(term)
    if not metrics:
        term += '*'
        metrics = raw_metric_query(term)

    if len(metrics) > 1 and is_all_leaves(metrics):
        metrics.insert(0, {'id': term, 'expandable': False})

    return metrics


def is_all_leaves(metrics):
    """Determine if all metrics are leaf nodes

    :type metrics: list
    :rtype: bool
    """
    all_leaves = True
    for metric in metrics:
        if metric['expandable']:
            all_leaves = False
            break
    return all_leaves


def get_graph_url(request):
    """Get graph url based on metric"""
    graph_args = {'title': 'Latest values for this metric', 'width': 600, 'height': 400}
    if 'metric' in request.GET:
        metric = request.GET['metric']
        if 'raw' in request.GET:
            graph = Graph(targets=[metric], **graph_args)
            return redirect(str(graph))
        else:
            return redirect(get_simple_graph_url([metric], **graph_args))

    return HttpResponse()
