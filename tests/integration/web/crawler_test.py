"""Webcrawler tests for reachability and HTML validation.

The crawler attempts to retrieve any NAV web UI page that can be reached with
parameterless GET requests, while logged in as an administrator.

In some respects, it would be preferable to generate 1 named test for each
reachable page, but the tests need to be generated during the test collection
phase, which means that a full web server needs to be running before pytest
runs - and it would also be preferable that the web server is started from a
fixture. Instead, the webcrawler is itself a fixture that allows iteration over
all reachable pages.
"""

from collections import namedtuple
from http.client import BadStatusLine
from lxml.html import fromstring

import pytest

from tidylib import tidy_document
from urllib.request import (
    HTTPCookieProcessor,
    Request,
    build_opener,
    install_opener,
    urlopen,
)
from urllib.error import HTTPError, URLError
from urllib.parse import (
    quote,
    urlencode,
    urljoin,
    urlparse,
    urlsplit,
    urlunparse,
)


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
    # getting these endpoints without args results in 400 bad request
    '/api/1/cam',
    '/api/1/arp',
    '/graphite',
]

#
# Web Crawler code and related utility functions
#

Page = namedtuple('Page', 'url response content_type content')


def normalize_path(url):
    url = urlsplit(url).path.rstrip('/')
    return '/' + url if not url.startswith('/') else url


class WebCrawler(object):
    blacklist = set(normalize_path(path) for path in BLACKLISTED_PATHS)

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.netloc = urlsplit(base_url).netloc
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

    def crawl_only_html(self):
        """Only yields crawled pages that have a content-type of html and is not
        blacklisted.
        """
        yield from filter(should_validate, self.crawl())

    def _visit_with_error_handling(self, url):
        try:
            page = self._visit(url)
        except HTTPError as error:
            content = error.fp.read()
            page = Page(url, error.code, error, content)
            self._add_seen(page)

        except URLError as error:
            page = Page(url, None, error, None)
            self._add_seen(page)

        except BadStatusLine as error:
            content = 'Server abruptly closed connection'
            page = Page(url, 500, error, content)
            self._add_seen(page)

        return page

    def _visit(self, url):
        if self._is_seen(url):
            return
        req = Request(_quote_url(url), headers={'Accept': 'text/html'})
        resp = urlopen(req, timeout=TIMEOUT)
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
            url = urlsplit(link)
            path = normalize_path(link)

            if url.scheme not in ['http', 'https']:
                continue
            elif url.netloc != self.netloc:
                continue
            elif element.tag in ('form', 'object') or attribute == 'style':
                continue
            elif self._is_blacklisted(path):
                continue
            elif element.attrib.get("rel") == "nofollow":
                continue  # ignore nofollow links
            elif not self._is_seen(path):
                self.queue.append('%s://%s%s' % (url.scheme, url.netloc, url.path))

    def login(self):
        login_url = urljoin(self.base_url, '/index/login/')
        opener = build_opener(HTTPCookieProcessor())
        data = urlencode({'username': self.username, 'password': self.password})
        opener.open(login_url, data.encode('utf-8'), TIMEOUT)
        install_opener(opener)

    def _add_seen(self, page, url=None):
        if not url:
            url = page.url
        url = normalize_path(url)
        self.seen_pages[url] = page

    def _is_seen(self, url):
        return normalize_path(url) in self.seen_pages

    def _is_blacklisted(self, url):
        path = normalize_path(url)
        for url in self.blacklist:
            if path.startswith(url):
                return True
        return False


def _quote_url(url):
    """Ensures non-ascii URL paths are quoted"""
    parsed = urlparse(url)
    try:
        parsed.path.encode('ascii')
    except UnicodeError:
        path = quote(parsed.path.encode('utf-8'))
    else:
        path = parsed.path
    quoted = (
        parsed.scheme,
        parsed.netloc,
        path,
        parsed.params,
        parsed.query,
        parsed.fragment,
    )
    return urlunparse(quoted)


#
# fixtures
#


@pytest.fixture(scope="session")
def webcrawler(gunicorn, admin_username, admin_password):
    crawler = WebCrawler(gunicorn, admin_username, admin_password)
    yield crawler


#
# test functions
#


def test_all_links_should_be_reachable(webcrawler):
    unreachable = []
    for page in webcrawler.crawl():
        if page.response != 200:
            # No need to fill up the test report files with contents of OK pages
            print(_content_as_string(page.content))
            unreachable.append(f"{page.url} ({page.response})")
    assert not unreachable, f"{len(unreachable)} unreachable pages:\n" + '\n'.join(
        unreachable
    )


def _content_as_string(content):
    if isinstance(content, str) or content is None:
        return content
    else:
        return content.decode('utf-8')


def test_page_should_be_valid_html(webcrawler):
    try:
        tidy_document("")
    except OSError as error:
        pytest.skip("tidylib is not available: {!r}".format(error))

    invalid = []
    for page in webcrawler.crawl_only_html():
        if page.response != 200 or not page.content:
            continue

        document, errors = tidy_document(page.content, TIDY_OPTIONS)
        errors = filter_errors(errors)
        if errors:
            print(f"{page.url} :")
            print(errors)
            invalid.append(page.url)

    assert not invalid, f"{len(invalid)} invalid HTML pages:\n" + '\n'.join(invalid)


def should_validate(page: Page):
    """Returns True if page is eligible for HTML validation, False if not"""
    if (
        page.response == 500
        or not page.content_type
        or not isinstance(page.content_type, str)
        or 'html' not in page.content_type.lower()
    ):
        return False
    path = normalize_path(page.url)
    for blacklisted_path in TIDY_BLACKLIST:
        if path.startswith(blacklisted_path):
            return False
    return True


def filter_errors(errors):
    if errors:
        return "\n".join(msg for msg in errors.split('\n') if not _should_ignore(msg))


def _should_ignore(msg):
    for ignore in TIDY_IGNORE:
        if ignore in msg:
            return True
    return False
