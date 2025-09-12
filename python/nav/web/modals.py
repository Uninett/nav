"""
Modal rendering utilities for Django HTMX applications.

This module provides utility functions for rendering and managing modal dialogs
in Django applications using HTMX. It includes functions for rendering modals
with custom templates, resolving modal content, and displaying alert messages
within modals.

Functions:
    render_modal: Render a modal dialog with a given template and context
    resolve_modal: Resolve a modal dialog with updated content
    render_modal_alert: Render an alert message within a modal dialog

Constants:
    DEFAULT_MODAL_ID: Default modal element ID ('modal')
    DEFAULT_MODAL_SIZE: Default modal size ('tiny')
"""

from typing import Optional

from django.shortcuts import render
from django_htmx.http import reswap, retarget

DEFAULT_MODAL_ID = 'modal'
DEFAULT_MODAL_SIZE = 'fit-content'


def render_modal(
    request,
    template_name: str,
    context: Optional[dict] = None,
    modal_id: Optional[str] = DEFAULT_MODAL_ID,
    size: Optional[str] = DEFAULT_MODAL_SIZE,
    show_close_button: bool = True,
    close_on_outside_click: bool = True,
):
    """Render a modal dialog with the given template and context"""

    if context is None:
        context = {}
    modal_context = {
        'modal_id': modal_id,
        'content_template': template_name,
        'modal_size': size,
        'show_close_button': show_close_button,
        'close_on_outside_click': close_on_outside_click,
        **context,
    }
    return render(request, 'modals/_nav_modal.html', modal_context)


def resolve_modal(
    request,
    template_name: Optional[str] = None,
    context: Optional[dict] = None,
    modal_id: Optional[str] = DEFAULT_MODAL_ID,
):
    """Resolve a modal dialog with the given template and context"""
    if context is None:
        context = {}
    modal_context = {'modal_id': modal_id, 'content_template': template_name, **context}
    return render(request, 'modals/_nav_modal_resolve.html', modal_context)


def render_modal_alert(
    request, message: str, modal_id: Optional[str] = DEFAULT_MODAL_ID
):
    """Render an alert box with the given message and swaps the modal content"""
    context = {
        'message': message,
        'modal_id': modal_id,
    }
    response = render(request, 'modals/_nav_modal_alert.html', context)
    reswap(response, 'outerHtml')
    retarget(response, f"#{modal_id}-alert")
    return response
