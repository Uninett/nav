from django.urls import reverse


def test_ipdevinfo_interface_details_should_support_typical_sysnames():
    assert reverse(
        'ipdevinfo-interface-details',
        args=('example-name123_underscore.example.org', '123'),
    )


def test_ipdevinfo_interface_details_should_support_ipv4_address():
    assert reverse('ipdevinfo-interface-details', args=('10.1.2.3', '123'))


def test_ipdevinfo_interface_details_should_support_ipv6_address():
    assert reverse('ipdevinfo-interface-details', args=('fe80::1234:abcd', '123'))


def test_ipdevinfo_interface_details_by_name_should_support_typical_sysnames():
    assert reverse(
        'ipdevinfo-interface-details-by-name',
        args=('example-name123_underscore.example.org', '123'),
    )


def test_ipdevinfo_interface_details_by_name_should_support_ipv4_address():
    assert reverse('ipdevinfo-interface-details-by-name', args=('10.1.2.3', '123'))


def test_ipdevinfo_interface_details_by_name_should_support_ipv6_address():
    assert reverse(
        'ipdevinfo-interface-details-by-name', args=('fe80::1234:abcd', '123')
    )
