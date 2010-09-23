from modpython_testcase import ModPythonTestCase
from nav.web.netmap import handler

class NetmapServerTest(ModPythonTestCase):
    module_under_test = handler

    def test_server_no_unicode_output(self):
        self.handler_outputs_no_unicode('/netmap/server')
