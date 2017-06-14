"""Webcrawler tests for reachability and HTML validation.

The crawler attempts to retrieve any NAV web UI page that can be reached with
parameterless GET requests, while logged in as an administrator.

We want one test for each such URL, but since generating more tests while
running existing tests isn't easily supported under pytest (yield tests are
becoming deprecated under pytest 4), the crawler is the de-facto reachability
tester. A dummy test will be generated for each seen URL, and the dummy tests
will assert that the response code of the URL was 200 OK.

In addition, HTML validation tests (using libtidy) will be generated for all
URLs that report a Content-Type of text/html.

"""
from __future__ import print_function

from collections import namedtuple
from lxml.html import fromstring
import os
import pytest
from tidylib import tidy_document
import urllib
import urllib2
import urlparse

HOST_URL = os.environ.get('TARGETURL', None)
USERNAME = os.environ.get('ADMINUSERNAME', 'admin')
PASSWORD = os.environ.get('ADMINPASSWORD', 'admin')
TIMEOUT = 90  # seconds?

TIDY_OPTIONS = {
    'doctype': 'auto',
    'output_xhtml': True,
    'input_encoding': 'utf8',
    'show-warnings': False,
}

TIDY_IGNORE = [
    # put list of error messages to ignore here (substring matches)
]

TIDY_BLACKLIST = [
    # put list of URIs to not run HTML validation for here
]

BLACKLISTED_PATHS = [
    '/cricket',
    '/index/logout',
    '/doc',
]

if not HOST_URL:
    pytest.skip(msg="Missing environment variable TARGETURL "
                    "(ADMINUSERNAME, ADMINPASSWORD) , skipping crawler tests!")


#
# Web Crawler code and related utility functions
#

Page = namedtuple('Page', 'url response content_type content')


def normalize_path(url):
    url = urlparse.urlsplit(url).path.rstrip('/')
    return '/' + url if not url.startswith('/') else url


class WebCrawler(object):
    blacklist = set(normalize_path(path) for path in BLACKLISTED_PATHS)

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.netloc = urlparse.urlsplit(base_url).netloc
        self.username = username
        self.password = password
        self.seen_pages = {}
        self.queue = []

    def crawl(self):
        if self.seen_pages:
            for page in self.seen_pages.values():
                yield page
            return

        self.login()
        self.queue.append(self.base_url)

        while self.queue:
            url = self.queue.pop()
            page = self._visit_with_error_handling(url)
            if page:
                yield page

    def _visit_with_error_handling(self, url):
        try:
            page = self._visit(url)
        except urllib2.HTTPError as error:
            content = error.fp.read()
            page = Page(url, error.code, error, content)
            self._add_seen(page)

        except urllib2.URLError as error:
            page = Page(url, None, error, None)
            self._add_seen(page)

        return page

    def _visit(self, url):
        if self._is_seen(url):
            return

        resp = urllib2.urlopen(url, timeout=TIMEOUT)
        content_type = resp.info()['Content-type']

        if 'html' in content_type.lower():
            content = resp.read()
            self._queue_links_from(content, url)
        else:
            content = None

        page = Page(url, resp.getcode(), content_type, content)
        self._add_seen(page)
        return page

    def _queue_links_from(self, content, base_url):
        html = fromstring(content)
        html.make_links_absolute(base_url)

        for element, attribute, link, pos in html.iterlinks():
            url = urlparse.urlsplit(link)
            path = normalize_path(link)

            if url.scheme not in ['http', 'https']:
                continue
            elif url.netloc != self.netloc:
                continue
            elif element.tag in ('form', 'object') or attribute == 'style':
                continue
            elif self._is_blacklisted(path):
                continue
            elif not self._is_seen(path):
                self.queue.append('%s://%s%s' % (url.scheme, url.netloc, url.path))

    def login(self):
        login_url = '%sindex/login/' % self.base_url
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        data = urllib.urlencode({'username': self.username,
                                 'password': self.password})
        opener.open(login_url, data, TIMEOUT)
        urllib2.install_opener(opener)

    def _add_seen(self, page, url=None):
        if not url:
            url = page.url
        url = normalize_path(url)
        self.seen_pages[url] = page

    def _is_seen(self, url):
        return normalize_path(url) in self.seen_pages

    def _is_blacklisted(self, url):
        return normalize_path(url) in self.blacklist


#
# test functions
#

crawler = WebCrawler(HOST_URL, USERNAME, PASSWORD)


def page_id(page):
    """Extracts a URL as a test id from a page"""
    return normalize_path(page.url)


@pytest.mark.parametrize("page", crawler.crawl(), ids=page_id)
def test_link_should_be_reachable(page):
    assert page.response == 200, page.content


@pytest.mark.parametrize("page", crawler.crawl(), ids=page_id)
def test_page_should_be_valid_html(page):
    if page.response != 200:
        pytest.skip("not validating non-reachable page")
    if not page.content_type or 'html' not in page.content_type.lower():
        pytest.skip("not attempting to validate non-html page")
    if not should_validate(page.url):
        pytest.skip("skip validation of blacklisted page")
    if not page.content:
        pytest.skip("page has no content")

    document, errors = tidy_document(page.content, TIDY_OPTIONS)
    errors = filter_errors(errors)

    assert not errors, "Found following validation errors:\n" + errors


def should_validate(url):
    path = normalize_path(url)
    for blacklisted_path in TIDY_BLACKLIST:
        if path.startswith(blacklisted_path):
            return False
    return True


def filter_errors(errors):
    if errors:
        return u"\n".join(msg for msg in errors.split(u'\n')
                          if not _should_ignore(msg))


def _should_ignore(msg):
    for ignore in TIDY_IGNORE:
        if ignore in msg:
            return True
    return False

