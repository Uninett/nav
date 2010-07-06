from lxml.html import fromstring
import socket
import urllib
import urllib2
import urlparse

socket.setdefaulttimeout(5)

host = 'elixis'
host_url = 'http://%s/' % host
login_url = '%sindex/login/' % host_url

blacklisted_paths = [
    '/cricket',
    '/index/logout',
]

seen_paths = {}
queue = [host_url]

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
data = urllib.urlencode({'username': 'admin', 'password': 's3cret'})
resp = opener.open(login_url, data)

def check_link(current_url):
    current_path = urlparse.urlsplit(current_url).path.rstrip('/')

    try:
        resp = opener.open(current_url)
    except urllib2.HTTPError, e:
        print seen_paths[current_path]
        raise e

    root = fromstring(resp.read())
    root.make_links_absolute(current_url)

    for element, attribute, link, pos in root.iterlinks():
        url = urlparse.urlsplit(link)
        path = url.path.rstrip('/')

        if url.scheme not in ['http', 'https']:
            continue
        elif url.hostname != host:
            continue
        elif element.tag in ('form', 'object') or attribute == 'style':
            continue
        elif path in blacklisted_paths:
            continue
        elif path not in seen_paths:
            queue.append('%s://%s%s' % (url.scheme, url.hostname, url.path))

        if path not in seen_paths:
            seen_paths[path] = []
        seen_paths[path].append((current_path, element, attribute))

def test_webpages():
    while queue:
        yield check_link, queue.pop()
