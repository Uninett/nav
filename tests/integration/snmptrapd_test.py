from unittest import TestCase
import signal
import time


class SnmptrapdSignalTest(TestCase):
    class TestIsOk(Exception):
        pass

    def setUp(self):
        def second_alarm(*_):
            print "Second ALRM signal received"
            raise self.TestIsOk()

        def first_alarm(*_):
            print "First ALRM signal received"
            signal.signal(signal.SIGALRM, second_alarm)
            signal.alarm(1)

        signal.signal(signal.SIGALRM, first_alarm)

    def tearDown(self):
        signal.signal(signal.SIGALRM, signal.SIG_DFL)

    def test_traplistener_does_not_raise_error_on_signals(self):
        from nav.snmptrapd.agent_pynetsnmp import TrapListener

        handler = TrapListener(('127.0.0.1', 0))
        signal.alarm(1)
        time.sleep(0.5)
        handler.open()
        try:
            self.assertRaises(self.TestIsOk,
                              handler.listen, 'public', lambda x, y: None)
        finally:
            handler.close()

