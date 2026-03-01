"""Selenium tests for ipdevinfo"""

from django.urls import reverse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_port_activity_graphs_load(selenium, base_url):
    """Verify that Activity Graphs load on the port details page."""

    path = reverse(
        'ipdevinfo-interface-details-by-name',
        kwargs={
            'netbox_sysname': 'example-sw.example.org',
            'port_name': '1',
        },
    )
    url = base_url + path
    selenium.get(url)

    wait = WebDriverWait(selenium, 20)
    tabs = wait.until(EC.visibility_of_element_located((By.ID, "port-details-tabs")))
    assert tabs.is_displayed()

    activity_tab_link = selenium.find_element(
        By.XPATH,
        "//div[@id='port-details-tabs']//ul/li/a[normalize-space()='Activity graphs']",
    )
    activity_tab_link.click()

    activity_panel = wait.until(
        EC.visibility_of_element_located((By.ID, "port-details-activity-graphs"))
    )
    assert activity_panel.is_displayed()

    graphite_graph = wait.until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                "#port-details-activity-graphs .graphitegraph[data-url]",
            )
        )
    )
    assert graphite_graph.is_displayed()
