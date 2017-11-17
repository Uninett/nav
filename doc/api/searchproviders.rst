-----------------------
NAVbar search providers
-----------------------

NAV's search bar (the one seen at the top of every NAV web page) provides a
pluggable architecture for search implementations. Any class that implements
the interface of :py:class:`nav.web.info.searchproviders.SearchProvider` can
be used as a provider of search results for the NAVbar.

The list of ``SearchProvider`` implementations that are used to respond to
NAVbar search is configured in NAV's Django settings. The default list, as of
NAV 4.8, looks like this:


.. code-block:: python

    # Classes that implement a search engine for the web navbar
    SEARCHPROVIDERS = [
	'nav.web.info.searchproviders.RoomSearchProvider',
	'nav.web.info.searchproviders.LocationSearchProvider',
	'nav.web.info.searchproviders.NetboxSearchProvider',
	'nav.web.info.searchproviders.InterfaceSearchProvider',
	'nav.web.info.searchproviders.VlanSearchProvider',
	'nav.web.info.searchproviders.PrefixSearchProvider',
	'nav.web.info.searchproviders.DevicegroupSearchProvider',
	'nav.web.info.searchproviders.UnrecognizedNeighborSearchProvider',
    ]

If you want to hook in your own SearchProvider, local to your installation,
you can do this by manipulating this list in your :file:`local_settings.py`
file.

A simple implementation example
-------------------------------

This is the current implementation of the Room search provider; it will do a
substring search among room IDs, and then return search results which link
back to each matched room's details page.

.. code-block:: python

    class RoomSearchProvider(SearchProvider):
	"""Searchprovider for rooms"""
	name = "Rooms"
	headers = [
	    ('Roomid', 'id'),
	    ('Description', 'description')
	]
	link = 'Roomid'

	def fetch_results(self):
	    results = Room.objects.filter(id__icontains=self.query).order_by("id")
	    for result in results:
		self.results.append(SearchResult(
		    reverse('room-info', kwargs={'roomid': result.id}),
		    result)
		)

The actual work of the implementation is accomplished within the
``fetch_results()`` method, which must return a list of
:py:class:`nav.web.info.searchproviders.SearchResult` namedtuples.

The ``headers`` class attribute defines how to extract columnar information
from the returned ``SearchResult``'s instance objects. In this case, the search
result tab for *Rooms* will contain two columns: One captioned *Roomid*, where
the cell values come from the Room objects' ``id`` attribute, and one
captioned *Description*, where the cell values come from the Room objects'
``description`` attributes.



The SearchProvider base class
-----------------------------

.. autoclass:: nav.web.info.searchproviders.SearchProvider
   :members:

The SearchResult namedtuple
---------------------------

A ``SearchResult`` namedtuple consist of the ``href`` and ``inst`` attributes.
``href`` is a URL used as a hyperlink on the search result line. ``inst`` is
normally some kind of instance object, typically a Django model, which
represent the search result itself.


.. autoclass:: nav.web.info.searchproviders.SearchResult
   :members:
