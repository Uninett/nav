from nav.ipdevpoll.plugins import paloaltoarp
from nav.ipdevpoll.plugins.paloaltoarp import parse_arp
from IPy import IP


def test_parse_mappings():
    assert (
        parse_arp(
            '''
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
        )
        == [
            ('ifindex', IP('192.168.0.1'), '00:00:00:00:00:01'),
            ('ifindex', IP('192.168.0.2'), '00:00:00:00:00:02'),
            ('ifindex', IP('192.168.0.3'), '00:00:00:00:00:03')
        ]
    )
