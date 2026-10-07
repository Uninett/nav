"""Playwright tests for the subnet matrix"""

from playwright.sync_api import expect


def test_when_clicking_a_subnet_cell_then_the_popover_should_load(authenticated_page):
    page, base_url = authenticated_page
    page.goto(f"{base_url}/report/matrix")

    cell = page.locator("td[data-netaddr='10.42.0.0/24']")
    cell.locator(".popover-trigger .fa-info-circle").click()

    content = cell.locator(".popover-content")
    expect(content).to_be_visible()
    expect(content.locator("h5")).to_have_text("10.42.0.0/24")
    expect(content).to_contain_text("netident: test lan")
    expect(content.locator(".usage-sparkline")).to_be_attached()
