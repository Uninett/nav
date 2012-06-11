from nav.ipdevpoll.storage import get_shadow_sort_order
from nav.ipdevpoll import shadows

# debateable whether this is a proper unit test, since it is in reality
# testing the functional combo of NetboxInfo.get_dependencies and
# nav.toposort.build_graph()
def test_netboxinfo_should_always_sort_last():
    classes = get_shadow_sort_order()
    assert classes[-1] is shadows.NetboxInfo
