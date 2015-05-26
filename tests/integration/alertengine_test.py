from nav.models.profiles import AlertSender
from nav.alertengine.dispatchers import Dispatcher


def test_all_handlers_should_be_loadable():
    for sender in AlertSender.objects.all():
        dispatcher = sender._load_dispatcher_class()
        assert issubclass(dispatcher, Dispatcher)
