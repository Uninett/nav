"""Playwright tests for netmap"""


def test_when_loading_netmap_then_it_should_not_have_syntax_errors(authenticated_page):
    page, base_url = authenticated_page
    errors = []
    page.on("pageerror", lambda error: errors.append(error))
    page.goto(f"{base_url}/netmap/")

    syntax_errors = [e for e in errors if "syntaxerror" in str(e).lower()]
    assert not syntax_errors, f"JavaScript syntax errors found: {syntax_errors}"
