from nav.eventengine.alerts import (
    get_list_of_templates_for,
    TemplateDetails,
    ensure_alert_templates_are_available,
    _render_template,
    AlertGenerator,
)
from mock import Mock
from django.template import loader


def test_should_be_able_to_find_snmpagentdown_alert_msg_templates():
    details = get_list_of_templates_for('snmpAgentState', 'snmpAgentDown')
    print(details)
    assert len(details) > 0
    assert all(isinstance(d, TemplateDetails) for d in details)


def test_should_be_able_to_load_snmpagentdown_alert_msg_template():
    details = TemplateDetails(
        name='snmpAgentState/snmpAgentDown-email.txt', msgtype='email', language='en'
    )
    ensure_alert_templates_are_available()
    template = loader.get_template(details.name)
    assert template


def test_should_be_able_to_render_snmpagentdown_alert_msg_template():
    details = TemplateDetails(
        name='snmpAgentState/snmpAgentDown-email.txt', msgtype='email', language='en'
    )
    ensure_alert_templates_are_available()
    event = Mock(varmap={})
    alert = AlertGenerator(event)
    _, output = _render_template(details, alert)
    assert output
