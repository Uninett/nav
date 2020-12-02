"""Selenium tests for netmap"""


def test_netmap_index_should_not_have_syntax_errors(selenium, base_url):
    selenium.get("{}/netmap/".format(base_url))
    log = selenium.get_log("browser")
    syntax_errors = [
        line
        for line in log
        if "syntaxerror" in line.get("message", "").lower()
        and line.get("source") == "javascript"
    ]
    assert not syntax_errors
