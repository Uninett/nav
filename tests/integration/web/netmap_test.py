import pytest
from django.core.urlresolvers import reverse


@pytest.mark.parametrize("layer", [2, 3])
def test_netmap_layer_graph_should_load(layer, client):
    url = reverse('netmap-graph', kwargs={'layer': layer})
    response = client.get(url)
    assert response.status_code == 200
