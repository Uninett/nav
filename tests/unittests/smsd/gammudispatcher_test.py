# mock/patch/hack/workaround: gammudispatcher normally requires gammu to be
# installed, but we're only testing functionality from the module that is not
# dependent on this. If there is no gammu module, we fake it so we can import
# gammudispather without failures.
import pytest
from mock import Mock, patch

from nav.smsd.dispatcher import PermanentDispatcherError, DispatcherError

try:
    import gammu
except ImportError:
    import sys

    # Mock a minimum gammu module when one isn't present to patch
    gammu = sys.modules['gammu'] = type(sys)('gammu')
    mock_statemachine = Mock(SendSMS=Mock(return_value=42))
    gammu.StateMachine = Mock(return_value=mock_statemachine)
    gammu.GSMError = Exception

from nav.smsd.gammudispatcher import decode_sms_to_unicode, GammuDispatcher

DUMMY_SENDSMS_ARGS = ("999999", ["Message 1", "Message 2"])


class TestThatDecodeSmsToUnicode:
    def test_should_decode_ascii_bytes_to_comparable_string(self):
        sms = 'Hello'
        unicode_sms = decode_sms_to_unicode(sms)
        assert sms == unicode_sms

    def test_should_decode_string_to_comparable_string(self):
        sms = 'A m\xf8\xf8se once bit my sister'
        unicode_sms = decode_sms_to_unicode(sms)
        assert sms == unicode_sms

    def test_should_decode_utf8_string_properly(self):
        sms = b'A m\xc3\xb8\xc3\xb8se once bit my sister'
        unicode_sms = decode_sms_to_unicode(sms)
        expected = 'A m\xf8\xf8se once bit my sister'
        assert unicode_sms == expected


class TestThatGammuDispatcher:
    def test_can_be_initialized(self):
        assert GammuDispatcher(None)

    @patch('gammu.StateMachine', new=Mock())
    def test_should_send_sms_without_error(self):
        dispatcher = GammuDispatcher(None)
        result = dispatcher.sendsms(*DUMMY_SENDSMS_ARGS)
        assert result

    def test_should_raise_permanent_error_when_gammu_cannot_read_config(self):
        mocked_statemachine = Mock(ReadConfig=Mock(side_effect=IOError('Fake')))
        with patch('gammu.StateMachine') as statemachine:
            statemachine.return_value = mocked_statemachine
            dispatcher = GammuDispatcher(None)
            with pytest.raises(PermanentDispatcherError):
                dispatcher.sendsms(*DUMMY_SENDSMS_ARGS)

    def test_should_raise_permanent_error_when_gammu_errors_during_init(
        self, mock_gsm_error
    ):
        mocked_statemachine = Mock(Init=Mock(side_effect=mock_gsm_error))
        with patch('gammu.StateMachine') as statemachine:
            statemachine.return_value = mocked_statemachine
            dispatcher = GammuDispatcher(None)
            with pytest.raises(PermanentDispatcherError):
                dispatcher.sendsms(*DUMMY_SENDSMS_ARGS)

    def test_should_raise_temporary_when_gammu_send_fails(self, mock_gsm_error):
        mocked_statemachine = Mock(SendSMS=Mock(side_effect=mock_gsm_error))
        with patch('gammu.StateMachine') as statemachine:
            statemachine.return_value = mocked_statemachine
            dispatcher = GammuDispatcher(None)
            with pytest.raises(DispatcherError):
                dispatcher.sendsms(*DUMMY_SENDSMS_ARGS)


@pytest.fixture(scope='module')
def mock_gsm_error():
    return gammu.GSMError({"Where": Mock(), 'Code': 666, 'Text': Mock()})
