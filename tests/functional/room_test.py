"""Selenium tests for room views"""

import os

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_room_image_upload(selenium, base_url):
    """Tests upload of an image to the standard room that comes with NAV"""
    # Photo by ChrisDag (CC BY 2.0)
    filedir = os.path.abspath(os.path.dirname(__file__))
    filename = "closet.jpg"
    filepath = os.path.join(filedir, filename)

    selenium.get("{}/search/room/myroom/upload/".format(base_url))
    upload = selenium.find_element(By.ID, "file")
    upload.send_keys(filepath)

    submit = selenium.find_element(
        By.XPATH, "//input[@type='submit' and @value='Upload selected images']"
    )
    submit.click()

    caption_present = WebDriverWait(selenium, 15).until(
        EC.text_to_be_present_in_element(
            (By.XPATH, "//li[@class='imagecardcontainer']//div//h5"), filename
        )
    )
    assert caption_present
