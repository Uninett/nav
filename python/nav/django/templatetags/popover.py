"""Template tags for popover components"""

from typing import Literal, Optional, get_args

from django import template
from django.utils.html import conditional_escape, format_html, mark_safe

register = template.Library()

# Valid values for enum-like parameters
TriggerElement = Literal['button', 'a', 'span']
Side = Literal['top', 'bottom', 'left', 'right']
Align = Literal['start', 'end']
Size = Literal['tiny', 'small', 'medium', 'large']

VALID_TRIGGER_ELEMENTS: tuple[TriggerElement, ...] = get_args(TriggerElement)
VALID_SIDES: tuple[Side, ...] = get_args(Side)
VALID_ALIGNS: tuple[Align, ...] = get_args(Align)
VALID_SIZES: tuple[Size, ...] = get_args(Size)


@register.inclusion_tag('components/popover/_confirm_popover.html', takes_context=True)
def confirm_popover(
    context: template.Context,
    popover_id: str,
    action_url: str,
    title: str = "Are you sure?",
    confirm_text: str = "Yes",
    cancel_text: str = "No",
    trigger_text: Optional[str] = None,
    trigger_icon: str = "fa-times-circle",
    trigger_classes: str = "secondary",
    size: Size = "tiny",
    side: Side = "bottom",
    align: Align = "start",
) -> dict:
    """Renders a confirmation popover with a form action.

    Usage::

        {% load popover %}
        {% confirm_popover popover_id="delete-item" action_url=delete_url %}

    :param context: Django template context
    :param popover_id: Unique identifier for the popover (required)
    :param action_url: URL for the form action (required)
    :param title: Confirmation question text
    :param confirm_text: Text for the confirm button
    :param cancel_text: Text for the cancel button
    :param trigger_text: If set, uses a button with this text instead of an icon
    :param trigger_icon: FontAwesome icon class (without 'fa' prefix)
    :param trigger_classes: CSS classes for the trigger button (default: secondary)
    :param size: Popover content size (tiny, small, medium, large)
    :param side: Position relative to trigger (top, bottom, left, right)
    :param align: Alignment (start, end)
    """
    return {
        'id': popover_id,
        'action_url': action_url,
        'title': title,
        'confirm_text': confirm_text,
        'cancel_text': cancel_text,
        'trigger_text': trigger_text,
        'trigger_icon': trigger_icon,
        'trigger_classes': trigger_classes,
        'size': size,
        'side': side,
        'align': align,
        'request': context.get('request'),
    }


@register.inclusion_tag('components/popover/_close_button.html')
def popover_close_button(text: str = "Cancel", classes: str = "secondary") -> dict:
    """Renders a close button for use inside popovers.

    Usage::

        {% load popover %}
        {% popover_close_button "Cancel" classes="secondary" %}

    :param text: Button text
    :param classes: Additional CSS classes for the button
    """
    return {
        'text': text,
        'classes': classes,
    }


class PopoverNode(template.Node):
    """Node for the {% popover %}...{% endpopover %} block tag."""

    def __init__(
        self,
        nodelist,
        id_var,
        trigger_text_var,
        trigger_element,
        trigger_classes,
        title_var,
        size,
        side,
        align,
        with_arrow,
    ):
        self.nodelist = nodelist
        self.id_var = id_var
        self.trigger_text_var = trigger_text_var
        self.trigger_element = trigger_element
        self.trigger_classes = trigger_classes
        self.title_var = title_var
        self.size = size
        self.side = side
        self.align = align
        self.with_arrow = with_arrow

    def render(self, context):
        id_value = self.id_var.resolve(context)
        trigger_text = self.trigger_text_var.resolve(context)
        title = self.title_var.resolve(context) if self.title_var else None
        trigger_classes = (
            self.trigger_classes.resolve(context) if self.trigger_classes else ""
        )

        # Content is trusted template output, not user input
        content = self.nodelist.render(context)

        arrow_class = "with-arrow" if self.with_arrow else ""
        side_attr = (
            format_html('data-side="{}"', self.side) if self.side != "bottom" else ""
        )
        align_attr = (
            format_html('data-align="{}"', self.align) if self.align != "start" else ""
        )

        trigger_html = _build_trigger_html(
            self.trigger_element,
            id_value,
            trigger_text,
            trigger_classes,
        )

        title_html = format_html("<h5>{}</h5>", title) if title else ""
        # side_attr and align_attr are already safe from format_html,
        # so mark the join as safe
        attrs = mark_safe(" ".join(filter(None, [side_attr, align_attr])))

        return format_html(
            '<div id="{}" class="popover {}" {}>\n'
            '  {}\n'
            '  <div class="popover-content {}">\n'
            '    {}\n'
            '    {}\n'
            '  </div>\n'
            '</div>',
            id_value,
            arrow_class,
            attrs,
            trigger_html,
            self.size,
            title_html,
            content,
        )


def _build_trigger_html(element, id_value, text, classes):
    """Build the HTML for the popover trigger element."""
    attrs = format_html(
        'data-popover-target="#{}" aria-haspopup="true" aria-expanded="false"',
        id_value,
    )
    text = conditional_escape(text)

    tag = {"button": "button", "a": "a"}.get(element, "span")
    if classes:
        return format_html('<{} class="{}" {}>{}</{}>', tag, classes, attrs, text, tag)
    return format_html('<{} {}>{}</{}>', tag, attrs, text, tag)


def _parse_popover_kwargs(bits, tag_name):
    """Parse keyword arguments from template tag tokens.

    :param bits: Token contents split by whitespace
    :param tag_name: Name of the tag (for error messages)
    :returns: Dictionary of keyword arguments
    :raises TemplateSyntaxError: If non-keyword arguments found or required args missing
    """
    kwargs = {}
    for bit in bits[1:]:
        if '=' in bit:
            key, value = bit.split('=', 1)
            kwargs[key] = value
        else:
            raise template.TemplateSyntaxError(
                f"'{tag_name}' tag requires keyword arguments"
            )

    if 'popover_id' not in kwargs:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' tag requires 'popover_id' argument"
        )
    if 'trigger_text' not in kwargs:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' tag requires 'trigger_text' argument"
        )

    return kwargs


def _validate_popover_params(trigger_element, size, side, align, tag_name):
    """Validate enum-like parameters for the popover tag.

    :raises TemplateSyntaxError: If any parameter has an invalid value
    """
    if trigger_element not in VALID_TRIGGER_ELEMENTS:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' trigger_element must be one of {VALID_TRIGGER_ELEMENTS}, "
            f"got '{trigger_element}'"
        )

    if size not in VALID_SIZES:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' size must be one of {VALID_SIZES}, got '{size}'"
        )

    if side not in VALID_SIDES:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' side must be one of {VALID_SIDES}, got '{side}'"
        )

    if align not in VALID_ALIGNS:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' align must be one of {VALID_ALIGNS}, got '{align}'"
        )


@register.tag('popover')
def do_popover(parser, token):
    """Block tag for generic popovers with custom content.

    Usage::

        {% load popover %}
        {% popover popover_id="info" trigger_text="About" title="About" %}
          <p>Custom content here...</p>
        {% endpopover %}

    :param popover_id: Unique identifier for the popover (required)
    :param trigger_text: Text/content for the trigger element (required)
    :param trigger_element: Element type: button (default), a, span
    :param trigger_classes: Additional CSS classes for the trigger
    :param title: Optional header text
    :param size: Content size (tiny, small, medium, large)
    :param side: Position (top, bottom, left, right)
    :param align: Alignment (start, end)
    :param with_arrow: Show pointing arrow (default: True)
    """
    bits = token.split_contents()
    tag_name = bits[0]

    kwargs = _parse_popover_kwargs(bits, tag_name)

    nodelist = parser.parse(('endpopover',))
    parser.delete_first_token()

    # Process arguments
    id_var = parser.compile_filter(kwargs['popover_id'])
    trigger_text_var = parser.compile_filter(kwargs['trigger_text'])
    trigger_element = _strip_quotes(kwargs.get('trigger_element', '"button"'))
    trigger_classes = (
        parser.compile_filter(kwargs['trigger_classes'])
        if 'trigger_classes' in kwargs
        else None
    )
    title_var = parser.compile_filter(kwargs['title']) if 'title' in kwargs else None
    size = _strip_quotes(kwargs.get('size', '"small"'))
    side = _strip_quotes(kwargs.get('side', '"bottom"'))
    align = _strip_quotes(kwargs.get('align', '"start"'))
    with_arrow = _parse_bool(kwargs.get('with_arrow', 'True'))

    _validate_popover_params(trigger_element, size, side, align, tag_name)

    return PopoverNode(
        nodelist,
        id_var,
        trigger_text_var,
        trigger_element,
        trigger_classes,
        title_var,
        size,
        side,
        align,
        with_arrow,
    )


def _strip_quotes(value):
    """Remove surrounding quotes from a string value."""
    if value and len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"') or (
            value[0] == "'" and value[-1] == "'"
        ):
            return value[1:-1]
    return value


def _parse_bool(value):
    """Parse a string value as boolean."""
    value = _strip_quotes(value).lower()
    if value in ('true', '1', 'yes'):
        return True
    if value in ('false', '0', 'no', ''):
        return False
    raise ValueError(f"Cannot parse '{value}' as boolean")
