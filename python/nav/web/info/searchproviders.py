from django.core.urlresolvers import reverse

from nav.models.manage import Room, Netbox
from nav.util import is_valid_ip
from nav.web.ipdevinfo.views import is_valid_hostname

class SearchResult():
    """
    Container for searchresults
    """
    def __init__(self, text, href, inst):
        self.text = text
        self.href = href
        self.inst = inst


class SearchProvider():
    """
    Searchprovider interface
    """
    name = "SearchProvider"

    def __init__(self, query=""):
        self.results = []
        self.query = query
        self.fetch_results()

    def fetch_results(self):
        """ Fetch results for the query """
        pass


class RoomSearchProvider(SearchProvider):
    """
    Searchprovider for rooms
    """
    name = "Rooms"

    def fetch_results(self):
        results = Room.objects.filter(id__icontains=self.query).order_by("id")
        for result in results:
            self.results.append(SearchResult(result.id,
                reverse('room-info', kwargs={'roomid': result.id}), result))


class NetboxSearchProvider(SearchProvider):
    """
    Searchprovider for netboxes
    """
    name = "Netboxes"

    def fetch_results(self):
        if is_valid_ip(self.query):
            results = Netbox.objects.filter(ip=self.query)
        else:
            results = Netbox.objects.filter(sysname__icontains=self.query)

        results.order_by("sysname")
        for result in results:
            self.results.append(SearchResult(result.sysname,
                reverse('ipdevinfo-details-by-name',
                    kwargs={'name': result.sysname}), result))


class FallbackSearchProvider(SearchProvider):
    """
    Fallback searchprovider if no results are found.
    Two cases:
    1 - if ip, send to ipdevinfos name lookup
    2 - if valid text based on ipdevinfos regexp, send to ipdevinfo
    """
    name = "Fallback"

    def fetch_results(self):
        if is_valid_ip(self.query):
            self.results.append(
                SearchResult(self.query, reverse('ipdevinfo-details-by-addr',
                    kwargs={'addr': self.query}), None))
        elif is_valid_hostname(self.query):
            self.results.append(
                SearchResult(self.query, reverse('ipdevinfo-details-by-name',
                    kwargs={'name': self.query}), None))
