from nav.tests.cases import ModPythonTestCase
from nav.web.netmap import views

class NetmapServerTest(ModPythonTestCase):
    module_under_test = views

    def test_server_no_unicode_output(self):
        self.handler_outputs_no_unicode('/netmap/server')
