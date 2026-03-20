"""Playwright tests for room views"""

import os

from playwright.sync_api import expect


def test_when_uploading_room_image_then_it_should_appear(authenticated_page):
    page, base_url = authenticated_page
    filedir = os.path.abspath(os.path.dirname(__file__))
    filename = "closet.jpg"
    filepath = os.path.join(filedir, filename)

    page.goto(f"{base_url}/search/room/myroom/upload/")
    page.locator("#file").set_input_files(filepath)
    page.locator("input[type='submit'][value='Upload selected images']").click()

    expect(page.locator("li.imagecardcontainer div h5")).to_contain_text(filename)
