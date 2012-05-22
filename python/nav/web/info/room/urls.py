from nav.web.info.room.views import search, roominfo
from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('',
    url(r'^$', search, name='room-search'),
    url(r'^(?P<roomid>[\w-]+)', roominfo, name='room-info')
)
