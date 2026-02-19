from django.test import TestCase

from nav.models.arnold import Justification
from nav.models.profiles import Account

from nav.auditlog import find_modelname
from nav.auditlog.models import LogEntry
from nav.auditlog.utils import get_auditlog_entries


class AuditlogModelTestCase(TestCase):
    def setUp(self):
        # This specific model is used because it is very simple
        self.justification = Justification.objects.create(name='testarossa')

    def test_str(self):
        LogEntry.add_log_entry(self.justification, 'str test', 'foo')
        log_entry = LogEntry.objects.filter(verb='str test').get()
        self.assertEqual(str(log_entry), 'foo')
        log_entry.delete()

    def test_add_log_entry_bad_template(self):
        with self.assertLogs(level='ERROR') as log:
            LogEntry.add_log_entry(
                self.justification, 'bad template test', 'this is a {bad} template'
            )
            log_entry = LogEntry.objects.filter(verb='bad template test').get()
            self.assertEqual(
                log_entry.summary, 'Error creating summary - see error log'
            )
            log_entry.delete()
            self.assertEqual(len(log.output), 1)
            self.assertEqual(len(log.records), 1)
            self.assertIn('KeyError when creating summary:', log.output[0])

    def test_add_log_entry_actor_only(self):
        LogEntry.add_log_entry(
            self.justification, 'actor test', 'actor "{actor}" only is tested'
        )
        log_entry = LogEntry.objects.filter(verb='actor test').get()
        self.assertEqual(log_entry.summary, 'actor "testarossa" only is tested')
        log_entry.delete()

    def test_add_create_entry(self):
        LogEntry.add_create_entry(self.justification, self.justification)
        log_entry = LogEntry.objects.filter(verb='create-justification').get()
        self.assertEqual(log_entry.summary, 'testarossa created testarossa')
        log_entry.delete()

    def test_add_delete_entry(self):
        LogEntry.add_delete_entry(self.justification, self.justification)
        log_entry = LogEntry.objects.filter(verb='delete-justification').get()
        self.assertEqual(log_entry.summary, 'testarossa deleted testarossa')
        log_entry.delete()

    def test_compare_objects(self):
        justification_1 = Justification.objects.create(
            name='ferrari', description='Psst!'
        )
        justification_2 = Justification.objects.create(name='lambo', description='Hush')
        LogEntry.compare_objects(
            self.justification,
            justification_1,
            justification_2,
            ('name', 'description'),
            ('description',),
        )
        log_entry = LogEntry.objects.filter(verb='edit-justification-name').get()
        self.assertEqual(
            log_entry.summary,
            'testarossa edited lambo: name changed from \'ferrari\' to \'lambo\'',
        )
        log_entry.delete()
        log_entry = LogEntry.objects.filter(verb='edit-justification-description').get()
        self.assertEqual(
            log_entry.summary, 'testarossa edited lambo: description changed'
        )
        log_entry.delete()

    def test_addLog_entry_before(self):
        LogEntry.add_log_entry(self.justification, 'actor test', 'blbl', before=1)
        log_entry = LogEntry.objects.filter(verb='actor test').get()
        self.assertEqual(log_entry.before, '1')
        log_entry.delete()

    def test_find_name(self):
        name = find_modelname(self.justification)
        self.assertEqual(name, 'blocked_reason')

    def test_when_log_entry_created_then_actor_sortkey_is_set(self):
        LogEntry.add_log_entry(
            self.justification, 'sortkey test', '{actor} did something'
        )
        log_entry = LogEntry.objects.filter(verb='sortkey test').get()
        self.assertEqual(log_entry.actor_sortkey, str(self.justification))

    def test_when_log_entry_has_object_then_object_sortkey_is_set(self):
        other = Justification.objects.create(name='object_test')
        LogEntry.add_log_entry(
            self.justification,
            'object sortkey test',
            '{actor} edited {object}',
            object=other,
        )
        log_entry = LogEntry.objects.filter(verb='object sortkey test').get()
        self.assertEqual(log_entry.object_sortkey, str(other))

    def test_when_log_entry_has_no_object_then_object_sortkey_is_null(self):
        LogEntry.add_log_entry(
            self.justification, 'no object test', '{actor} did something'
        )
        log_entry = LogEntry.objects.filter(verb='no object test').get()
        self.assertIsNone(log_entry.object_sortkey)

    def test_when_log_entry_has_target_then_target_sortkey_is_set(self):
        obj = Justification.objects.create(name='target_obj')
        target = Justification.objects.create(name='target_test')
        LogEntry.add_log_entry(
            self.justification,
            'target sortkey test',
            '{actor} sent {object} to {target}',
            object=obj,
            target=target,
        )
        log_entry = LogEntry.objects.filter(verb='target sortkey test').get()
        self.assertEqual(log_entry.target_sortkey, str(target))

    def test_when_log_entry_has_no_target_then_target_sortkey_is_null(self):
        LogEntry.add_log_entry(
            self.justification, 'no target test', '{actor} did something'
        )
        log_entry = LogEntry.objects.filter(verb='no target test').get()
        self.assertIsNone(log_entry.target_sortkey)


class AuditlogUtilsTestCase(TestCase):
    def setUp(self):
        # This specific model is used because it is very simple
        self.justification = Justification.objects.create(name='testarossa')

    def test_get_auditlog_entries(self):
        modelname = 'blocked_reason'  # Justification's db_table
        justification_1 = Justification.objects.create(name='j1')
        justification_2 = Justification.objects.create(name='j2')
        LogEntry.add_create_entry(self.justification, justification_1)
        LogEntry.add_log_entry(
            self.justification,
            'greet',
            '{actor} greets {object}',
            object=justification_2,
            subsystem="hello",
        )
        LogEntry.add_log_entry(
            self.justification,
            'deliver',
            '{actor} delivers {object} to {target}',
            object=justification_1,
            target=justification_2,
            subsystem='delivery',
        )
        entries = get_auditlog_entries(modelname=modelname)
        self.assertEqual(entries.count(), 3)
        entries = get_auditlog_entries(modelname=modelname, subsystem='hello')
        self.assertEqual(entries.count(), 1)
        entries = get_auditlog_entries(modelname=modelname, pks=[justification_1.pk])
        self.assertEqual(entries.count(), 2)


def test_v1_api_returns_plain_strings_for_backward_compatibility(db, token, api_client):
    """Test that v1 API returns plain strings (backward compatibility)"""
    # Configure token to allow access to v1 auditlog endpoint
    token.endpoints = {'auditlog': '/auditlog/'}
    token.save()

    # Create an account that will be the actor
    account = Account.objects.create(
        login='testuser', name='Test User', password='unused'
    )
    # Create a justification as the object
    justification = Justification.objects.create(name='test_object')

    # Create a log entry
    entry = LogEntry.add_log_entry(
        account,
        'test-action',
        '{actor} performed action on {object}',
        object=justification,
    )

    # Fetch the entry via v1 API
    response = api_client.get(f'/api/1/auditlog/{entry.id}/')

    assert response.status_code == 200
    data = response.json()

    # Verify v1 returns plain strings
    assert isinstance(data['actor'], str)
    assert data['actor'] == 'testuser'
    assert isinstance(data['object'], str)
    assert data['object'] == 'test_object'


def test_v2_api_retrieve_returns_entity_objects_with_urls(db, token, api_client):
    """Test that v2 retrieve endpoint returns objects with {name, url}"""
    # Configure token to allow access to v2 auditlog endpoint
    # Note: TokenPermission.version=1 strips /api/1, so v2 paths become /2/auditlog/
    token.endpoints = {'auditlog': '/2/auditlog/'}
    token.save()

    # Create an account that will be the actor (accounts have get_absolute_url)
    account = Account.objects.create(
        login='testuser', name='Test User', password='unused'
    )
    # Create a justification as the object
    justification = Justification.objects.create(name='test_object')

    # Create a log entry
    entry = LogEntry.add_log_entry(
        account,
        'test-action',
        '{actor} performed action on {object}',
        object=justification,
    )

    # Fetch the entry via v2 API retrieve endpoint
    response = api_client.get(f'/api/2/auditlog/{entry.id}/')

    assert response.status_code == 200
    data = response.json()

    # Verify actor has both name and url
    assert isinstance(data['actor'], dict)
    assert data['actor']['name'] == 'testuser'
    assert data['actor']['url'] is not None
    assert '/useradmin/account/' in data['actor']['url']

    # Verify object has name (url may be None if Justification lacks get_absolute_url)
    assert isinstance(data['object'], dict)
    assert data['object']['name'] == 'test_object'


def test_v2_api_list_returns_entity_objects_with_urls(db, token, api_client):
    """Test that v2 list endpoint returns objects with {name, url}"""
    # Configure token to allow access to v2 auditlog endpoint
    # Note: TokenPermission.version=1 strips /api/1, so v2 paths become /2/auditlog/
    token.endpoints = {'auditlog': '/2/auditlog/'}
    token.save()

    # Create an account that will be the actor
    account = Account.objects.create(
        login='testuser', name='Test User', password='unused'
    )
    # Create a justification as the object
    justification = Justification.objects.create(name='test_object')

    # Create a log entry
    LogEntry.add_log_entry(
        account,
        'test-action',
        '{actor} performed action on {object}',
        object=justification,
    )

    # Fetch entries via v2 API list endpoint
    response = api_client.get('/api/2/auditlog/')

    assert response.status_code == 200
    data = response.json()
    assert len(data['results']) > 0

    # Check the first entry
    first_entry = data['results'][0]
    assert isinstance(first_entry['actor'], dict)
    assert 'name' in first_entry['actor']
    assert 'url' in first_entry['actor']
