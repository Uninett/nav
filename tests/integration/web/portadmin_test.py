from django.urls import reverse
from django.utils.encoding import smart_str


class TestFeedbackModal:
    def test_should_render_feedback_modal(self, client):
        url = reverse('portadmin-feedback-modal')
        response = client.get(url)
        assert 'id="portadmin-feedback-modal"' in smart_str(response.content)
