#!/usr/bin/env python
"""Crawls test instance of NAV and report any errors.

The basic crawler code enumerates all pages paths that can be reached by GET
queries without parameters while logged in as an administrator. HTML for all
pages that report Content-type html are stored an validated by tidy in an
additional test.

"""
from lxml.html import fromstring
import os
import pytest
import tidy
import urllib
import urllib2
import urlparse
import time
from itertools import chain

HOST_URL = os.environ.get('TARGETURL', None)
USERNAME = os.environ.get('ADMINUSERNAME', 'admin')
PASSWORD = os.environ.get('ADMINPASSWORD', 'admin')

TIDY_OPTIONS = {
    'doctype': 'auto',
    'output_xhtml': True,
    'input_encoding': 'utf8',
    'show-warnings': False,
}

TIDY_IGNORE = [
    'trimming empty <option>',
    'trimming empty <i>',
    '<table> lacks "summary" attribute',
]

TIDY_BLACKLIST = [
]

BLACKLISTED_PATHS = [
    '/cricket',
    '/index/logout',
    '/doc',
]

if not HOST_URL:
    pytest.skip(msg="Missing environment variable TARGETURL (ADMINUSERNAME, ADMINPASSWORD) , skipping crawler tests!")

TIMEOUT = 90
HOST = urlparse.urlsplit(HOST_URL).hostname

seen_paths = {}
html_store = {}
queue = [HOST_URL]

def test_webpages():
    result = login()
    if result:
        func, args = result[0], result[1:]
        func(*args)
    register_seen(HOST_URL)
    while queue:
        url = queue.pop()
        yield ('is %s reachable' % url2path(url),) + check_response(url)

    for url in html_store.keys():
        yield "does %s validate" % url2path(url), check_validates, url


def url2path(url):
    """Strips everything but the path, query and fragment of a full URL"""
    uri = urlparse.urlsplit(url)
    uri = urlparse.SplitResult('', '', uri.path, uri.query, uri.fragment)
    uri = urlparse.urlunsplit(uri)
    return uri


def handle_http_error(func):
    def _decorator(*args, **kwargs):
        starttime = time.time()
        funcinfo = "%s(%s)" % (func.__name__,
                               ", ".join(map(repr,
                                             chain(args, kwargs.values()))))
        fmt = "%s - %s used %s seconds"
        try:
            return func(*args, **kwargs)
        except urllib2.HTTPError, error:
            print fmt % ('HttpError', funcinfo, time.time() - starttime)
            print "%s :" % error.url
            print "-" * (len(error.url)+2)
            return failure, error.url, error.code, error
        except urllib2.URLError, error:
            print fmt % ('URLError', funcinfo, time.time() - starttime)
            return urlerror, error

    return _decorator

def failure(url, code, error):
    print error.fp.read()
    assert code == 200

def success(url):
    assert True

def urlerror(error):
    raise error

@handle_http_error
def login():
    login_url = '%sindex/login/' % HOST_URL
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    data = urllib.urlencode({'username': USERNAME, 'password': PASSWORD})
    opener.open(login_url, data, TIMEOUT)
    urllib2.install_opener(opener)
    return success, login_url

def get_path(url):
    return urlparse.urlsplit(url).path.rstrip('/')

def is_html(resp):
    return 'html' in resp.info()['Content-type'].lower()

def should_validate(url):
    path = get_path(url)
    for blacklisted_path in TIDY_BLACKLIST:
        if path.startswith(blacklisted_path):
            return False
    return True

def retrieve_links(current_url):
    root = fromstring(html_store[current_url])
    root.make_links_absolute(current_url)

    for element, attribute, link, pos in root.iterlinks():
        url = urlparse.urlsplit(link)
        path = get_path(link)

        if url.scheme not in ['http', 'https']:
            continue
        elif url.hostname != HOST:
            continue
        elif element.tag in ('form', 'object') or attribute == 'style':
            continue
        elif path in BLACKLISTED_PATHS:
            continue
        elif not has_been_seen(path):
            queue.append('%s://%s%s' % (url.scheme, url.netloc, url.path))


        register_seen(path, current_url)

def filter_errors(errors):
    return filter(lambda e: e.message not in TIDY_IGNORE, errors)

@handle_http_error
def check_response(current_url):
    resp = urllib2.urlopen(current_url, timeout=TIMEOUT)

    if is_html(resp):
        html_store[current_url] = resp.read()
        retrieve_links(current_url)
    return success, current_url

def has_been_seen(url):
    return get_path(url) in seen_paths

def register_seen(seen_url, source_url=None):
    seen_url = get_path(seen_url)
    if seen_url not in seen_paths:
        seen_paths[seen_url] = []
    if source_url:
        seen_paths[seen_url].append(source_url)


def check_validates(url):
    if not should_validate(url):
        return

    errors = tidy.parseString(html_store[url], **TIDY_OPTIONS).errors
    errors = filter_errors(errors)

    if errors:
        errors.insert(0, 'Found following validation errors:')
        raise Exception(u'\n'.join([unicode(e) for e in errors]))
