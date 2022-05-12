
from nav.eventengine.plugin import EventHandler
from nav.eventengine.alerts import AlertGenerator
from nav.models.manage import Device

"""deviceState handler plugin"""

class DeviceStateHandler(EventHandler):
    """Accepts deviceState events"""


    handled_types = ('deviceState',)

    def handle(self):
        event = self.event
        self._post_alert(event)
        event.delete()

    def get_target(self):
        return self.event.device

    def _post_alert(self, event):
        alert = AlertGenerator(event)
        if not alert.alert_type:
            self._logger.error(
                "%s: Alert for event %s discarded because of missing alert type",
                self.get_target(),
                event,
            )
            return
        alert.post()
