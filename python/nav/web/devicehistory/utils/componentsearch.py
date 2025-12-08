from typing import Union

from django.db.models import Model, Q, QuerySet
from nav.models.manage import Netbox, Module, Location, NetboxGroup, Room, Device


def get_component_search_results(
    search: str, button_text: str, exclude: list[type[Model]] = []
):
    """
    Retrieves grouped search results for component types based on a search query.

    :param search: The search term to filter components.
    :param button_text: A format string for the button label, which will be formatted
        with the component type label. It should contain exactly one '%s' placeholder.

    :param exclude: A list of component types to exclude from the search.
        Defaults to an empty list.
    :returns: Dictionary mapping component names to dictionaries with the
        following keys:

        - **label** (*str*): Display label for the component type.
        - **has_grouping** (*bool*): Indicates if the results are grouped.
        - **values** (*list or list of tuples*): Grouped or ungrouped search results.
        - **button** (*str*): Label for the associated action button.
    """
    if button_text.count('%s') != 1:
        raise ValueError("button_text must contain exactly one '%s' placeholder")

    results = {}
    searches = _get_search_queries(search, exclude)

    for component_type, query, group_by in searches:
        component_query = _get_component_query(component_type, query)
        component_results = _prefetch_and_group_components(
            component_type, component_query, group_by
        )

        if component_results:
            component_name = _get_component_name(component_type)
            component_label = _get_component_label(component_type)
            results[component_name] = {
                'label': component_label,
                'values': component_results,
                'has_grouping': group_by is not None,
                'button': button_text % component_label,
            }
    return results


def _get_search_queries(search: str, exclude: list[Model] = []):
    """
    Constructs a list of search queries for different component types.

    Excludes specified component types if provided.
    """
    searches: list[tuple[type[Model], Q, type[Model] | None]] = [
        (Location, Q(id__icontains=search), None),
        (Room, Q(id__icontains=search), Location),
        (
            Netbox,
            Q(sysname__icontains=search)
            | Q(entities__device__serial__icontains=search),
            Room,
        ),
        (NetboxGroup, Q(id__icontains=search), None),
        (
            Module,
            Q(name__icontains=search) | Q(device__serial__icontains=search),
            Netbox,
        ),
        (
            Device,
            Q(
                serial__icontains=search,
                entities__isnull=True,
                power_supplies_or_fans__isnull=True,
                modules__isnull=True,
            ),
            None,
        ),
    ]
    if exclude:
        searches = [
            (component_type, query, group_by)
            for component_type, query, group_by in searches
            if component_type not in exclude
        ]
    return searches


def _get_component_query(component_type: Model, query: Q):
    """
    Constructs a query result for the specified component type based on
    the provided query.
    """
    if component_type._meta.db_table == "netbox":
        return Netbox.objects.with_chassis_serials().filter(query).distinct()
    return component_type.objects.filter(query)


def _prefetch_and_group_components(
    component_type: Model, query_results: QuerySet, group_by: Union[Model, None] = None
):
    """
    Prefetches related objects and groups the results by the specified group_by model.

    If group_by is None, returns a flat list of component IDs and labels.
    If group_by is specified, groups the results by the related model's
    string representation.
    """
    if group_by is None or not hasattr(component_type, group_by._meta.db_table):
        return [
            (component.id, _get_option_label(component)) for component in query_results
        ]

    group_by_name = group_by._meta.db_table
    component_results = query_results.prefetch_related(group_by_name)
    grouped_results = {}
    for component in component_results:
        group_by_model = getattr(component, group_by_name)
        group_name = str(group_by_model)
        option = (component.id, _get_option_label(component))

        if group_name not in grouped_results:
            grouped_results[group_name] = []
        grouped_results[group_name].append(option)
    return [(group, components) for group, components in grouped_results.items()]


def _get_option_label(component: Model):
    """
    Returns a string representation of the component for use in option labels.
    """
    if component._meta.db_table == 'netbox':
        return '%(sysname)s [%(ip)s - %(chassis_serial)s]' % component.__dict__
    return str(component)


def _get_component_name(component_type: Model):
    """
    Returns the name of a component based on its type.
    """
    if component_type._meta.db_table == 'device':
        return 'inactive_device'
    return component_type._meta.db_table


def _get_component_label(component_type: Model):
    """
    Returns the label for a component based on its type.
    """
    if component_type._meta.db_table == 'device':
        return 'Inactive Device'
    return component_type._meta.verbose_name.title()
