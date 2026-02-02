"""Template tags for popover components"""

from django import template
from django.utils.html import conditional_escape, format_html, mark_safe

register = template.Library()


@register.inclusion_tag('components/popover/_confirm_popover.html', takes_context=True)
def confirm_popover(
    context,
    popover_id,
    action_url,
    title="Are you sure?",
    confirm_text="Yes",
    cancel_text="No",
    trigger_text=None,
    trigger_icon="fa-times-circle",
    trigger_classes="secondary",
    size="tiny",
    side="bottom",
    align="start",
):
    """Renders a confirmation popover with a form action.

    Usage::

        {% load popover %}
        {% confirm_popover popover_id="delete-item" action_url=delete_url %}

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
def popover_close_button(text="Cancel", classes="secondary"):
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

    if element == "button":
        if classes:
            return format_html(
                '<button class="{}" {}>{}</button>', classes, attrs, text
            )
        return format_html('<button {}>{}</button>', attrs, text)
    elif element == "a":
        if classes:
            return format_html('<a class="{}" {}>{}</a>', classes, attrs, text)
        return format_html('<a {}>{}</a>', attrs, text)
    else:
        if classes:
            return format_html('<span class="{}" {}>{}</span>', classes, attrs, text)
        return format_html('<span {}>{}</span>', attrs, text)


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

    # Parse keyword arguments
    kwargs = {}
    for bit in bits[1:]:
        if '=' in bit:
            key, value = bit.split('=', 1)
            kwargs[key] = value
        else:
            raise template.TemplateSyntaxError(
                f"'{tag_name}' tag requires keyword arguments"
            )

    # Required arguments
    if 'popover_id' not in kwargs:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' tag requires 'popover_id' argument"
        )
    if 'trigger_text' not in kwargs:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' tag requires 'trigger_text' argument"
        )

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

    # Validate enum-like parameters
    valid_trigger_elements = ('button', 'a', 'span')
    if trigger_element not in valid_trigger_elements:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' trigger_element must be one of {valid_trigger_elements}, "
            f"got '{trigger_element}'"
        )

    valid_sides = ('top', 'bottom', 'left', 'right')
    if side not in valid_sides:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' side must be one of {valid_sides}, got '{side}'"
        )

    valid_aligns = ('start', 'end')
    if align not in valid_aligns:
        raise template.TemplateSyntaxError(
            f"'{tag_name}' align must be one of {valid_aligns}, got '{align}'"
        )

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
    value = _strip_quotes(value)
    return value.lower() not in ('false', '0', 'no', '')
