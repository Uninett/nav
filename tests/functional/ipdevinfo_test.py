"""Playwright tests for ipdevinfo"""

from playwright.sync_api import expect


def test_when_loading_port_details_activity_graphs_should_load(authenticated_page):
    """Verify that Activity Graphs load on the port details page."""

    page, base_url = authenticated_page
    page.goto(
        f"{base_url}/ipdevinfo/test-gsw.example.org/interface=1/#port-details-activity-graphs"
    )

    activity_tab = page.locator("#port-details-activity-graphs")
    expect(activity_tab).to_be_visible()

    graphite_graphs = activity_tab.locator(".graphitegraph[data-url]")
    expect(graphite_graphs).to_have_count(6)

    rickshaw_containers = activity_tab.locator(".graphitegraph .rickshaw-container")
    expect(rickshaw_containers).to_have_count(6)

    # Assume that graphs are loaded if every container has non-zero width and height
    for i in range(rickshaw_containers.count()):
        expect(rickshaw_containers.nth(i)).to_be_visible()
        box = rickshaw_containers.nth(i).bounding_box()
        assert box["width"] > 0, f"Graph {i} width is zero"
        assert box["height"] > 0, f"Graph {i} height is zero"
