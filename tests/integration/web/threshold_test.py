from django.urls import reverse
from django.utils.encoding import smart_str


class TestThresholdModalView:
    def test_should_render_threshold_help_modal(self, client):
        url = reverse('threshold-help-modal')
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="threshold-help-modal"' in smart_str(response.content)
