#!/usr/bin/env python

from lxml.html import fromstring
import os
import socket
import tidy
import urllib
import urllib2
import urlparse

'''
Crawls test instance of NAV and report any errors.

The basic crawler code enumerates all pages paths that can be reached by GET
queries without parameters while logged in as an administrator. HTML for all
pages that report Content-type html are stored an validated by tidy in an
additional test.
'''

HOST_URL = os.environ['TARGETURL']
USERNAME = os.environ.get('ADMINUSERNAME', 'admin')
PASSWORD = os.environ['ADMINPASSWORD']

TIDY_OPTIONS = {
    'doctype': 'strict',
    'output_xhtml': True,
    'input_encoding': 'utf8',
}

TIDY_IGNORE = [
    'trimming empty <option>',
    '<table> lacks "summary" attribute',
]

TIDY_BLACKLIST = [
    '/seeddb',
]

BLACKLISTED_PATHS = [
    '/cricket',
    '/index/logout',
]

socket.setdefaulttimeout(5)

HOST = urlparse.urlsplit(HOST_URL).hostname

seen_paths = {}
html_store = {}
queue = [HOST_URL]

def test_webpages():
    login()
    while queue:
        yield check_response, queue.pop()

def test_validates():
    for url in html_store.keys():
        yield check_validates, url

def handle_http_error(func):
    def _decorator(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except urllib2.HTTPError, error:
            print "%s :" % error.url
            print "-" * (len(error.url)+2)
            print error.fp.read()
            raise

    return _decorator

@handle_http_error
def login():
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    data = urllib.urlencode({'username': USERNAME, 'password': PASSWORD})
    resp = opener.open('%sindex/login/' % HOST_URL, data)
    urllib2.install_opener(opener)

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
        elif path not in seen_paths:
            queue.append(link)

        if path not in seen_paths:
            seen_paths[path] = []
        seen_paths[path].append((get_path(current_url), element, attribute))

def filter_errors(errors):
    return filter(lambda e: e.message not in TIDY_IGNORE, errors)

@handle_http_error
def check_response(current_url):
    resp = urllib2.urlopen(current_url)

    if is_html(resp):
        html_store[current_url] = resp.read()
        retrieve_links(current_url)

def check_validates(url):
    if not should_validate(url):
        return

    errors = tidy.parseString(html_store[url], **TIDY_OPTIONS).errors
    errors = filter_errors(errors)

    if errors:
        errors.insert(0, 'Found following validation errors:')
        raise Exception(u'\n'.join([unicode(e) for e in errors]))
