import pytest
import pytest_twisted

from mock import Mock

from nav.ipdevpoll.plugins import paloaltoarp, plugin_registry
from nav.ipdevpoll.jobs import JobHandler, SuggestedReschedule


class paloaltoarp_test(paloaltoarp.PaloaltoArp):
    def __init__(self, *args, **kwargs):

        self.config = ''

        self.paloalto_devices = [{'key': 'abcdefghijklmnopqrstuvwxyz1234567890', 'hostname': '127.0.0.1'}]

        # put the mappings in a list so we can verify them
        self.mappings = []

        super().__init__(*args, **kwargs)

    def _do_request(self, ip, key):
        return b'''
<response status="success">
   <result>  
        <max>132000</max>  
        <total>3</total>  
        <timeout>1800</timeout>  
        <dp>s3dp1</dp>  
        <entries>  
            <entry>  
                <status>  s  </status>  
                <ip>192.168.0.1</ip>  
                <mac>00:00:00:00:00:01</mac>  
                <ttl>100</ttl>  
                <interface>ae2</interface>  
                <port>ae2</port>  
            </entry>  
            <entry>  
                <status>  e  </status>  
                <ip>192.168.0.2</ip>  
                <mac>00:00:00:00:00:02</mac>  
                <ttl>200</ttl>  
                <interface>ae2</interface>  
                <port>ae2</port>  
            </entry> 
            <entry>  
                <status>  c  </status>  
                <ip>192.168.0.3</ip>  
                <mac>00:00:00:00:00:03</mac>  
                <ttl>300</ttl>  
                <interface>ae3.61</interface>  
                <port>ae3</port>  
            </entry>  
            <entry>  
                <status>  i  </status>  
                <ip>192.168.0.4</ip>  
                <mac>00:00:00:00:00:04</mac>  
                <ttl>400</ttl>  
                <interface>ae3.61</interface>  
                <port>ae3</port>  
            </entry> 
        </entries>  
    </result> 
</response> 
'''

    # override the _process_data method and verify the input mappings
    def _process_data(self, mappings):
        self.mappings = mappings


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_process_arp_data():
    plugin = paloaltoarp_test()

    plugin_registry['paloaltoarp'] = plugin
    job = JobHandler('paloaltoarp', 'localhost', plugins=['paloaltoarp'])
    agent = Mock()
    job.agent = agent
    job._create_agentproxy = Mock()
    job._destroy_agentproxy = Mock()

    assert plugin.mappings == []
