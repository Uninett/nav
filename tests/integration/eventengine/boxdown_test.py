"""Black-box integration tests for the apparent proper processing of boxState events"""

import os

import pytest

from nav.eventengine import get_eventengine_output


def test_eventengine_should_declare_box_down(host_going_down, eventengine_test_config):
    post_fake_boxdown(host_going_down)

    # Dump the eventq table for debugging
    _dump_eventq_table()

    get_eventengine_output(6)
    states = host_going_down.get_unresolved_alerts("boxState")
    assert states.count() > 0, "netbox has not been marked as down"


########################
#                      #
# fixtures and helpers #
#                      #
########################
def post_fake_boxdown(netbox):
    # Import Django models after database is available
    from nav.models.event import EventQueue as Event

    event = Event(
        source_id="pping",
        target_id="eventEngine",
        event_type_id="boxState",
        netbox=netbox,
        state=Event.STATE_START,
    )
    event.save()


@pytest.fixture()
def host_going_down(postgresql):
    # Import Django models after database is available
    from nav.models.manage import Netbox

    box = Netbox(
        ip="10.254.254.254",
        sysname="downhost.example.org",
        organization_id="myorg",
        room_id="myroom",
        category_id="SRV",
    )
    box.save()
    yield box
    print("teardown test device")
    box.delete()


def _dump_eventq_table():
    """Dump eventq table contents for debugging"""
    import subprocess
    from django.conf import settings

    # Get database configuration from Django settings
    db_config = settings.DATABASES['default']
    env = {
        'PGHOST': db_config.get('HOST'),
        'PGUSER': db_config.get('USER'),
        'PGDATABASE': db_config.get('NAME'),
        'PGPORT': str(db_config.get('PORT')),
        'PGPASSWORD': db_config.get('PASSWORD'),
    }
    print(f"env for dump: {env!r}")
    try:
        result = subprocess.run(
            ['psql', '-c', 'SELECT * FROM eventq ORDER BY time DESC;'],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        print("=== EventQ Table Contents ===")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print("=============================")
    except Exception as e:  # noqa: BLE001
        print(f"Failed to dump eventq table: {e}")


@pytest.fixture(scope="module")
def eventengine_test_config(configuration_dir):
    print("placing temporary eventengine config")
    configfile = configuration_dir / "eventengine.conf"
    tmpfile = configfile.with_suffix(".bak")
    os.rename(configfile, tmpfile)
    with open(configfile, "w") as config:
        config.write(
            """
[timeouts]
boxDown.warning = 1s
boxDown.alert = 2s
"""
        )
    yield configfile
    print("restoring eventengine config")
    os.remove(configfile)
    os.rename(tmpfile, configfile)
