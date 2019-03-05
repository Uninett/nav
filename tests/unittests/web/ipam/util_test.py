import unittest
from IPy import IPSet, IP
from nav.web.ipam.util import suggest_range, \
    partition_subnet, _get_available_subnets


class IpamUtilTest(unittest.TestCase):

    def test_partition_subnet(self):
        prefix = IP("10.0.0.0/8")
        partitions = partition_subnet(24, prefix)
        # partition_subnet returns a lazy sequence, so let`s step through it
        partition = next(partitions)
        # should round partition to nearest power of two
        self.assertEqual(partition.len(), 256)
        # should be a part of the partitioned prefix
        self.assertTrue(partition in prefix)
        # TODO: test for number of partitions?

    def test_partition_subnet6(self):
        prefix = IP("fe80::/40")
        partitions = partition_subnet(64, prefix)
        # partition_subnet returns a lazy sequence, so let`s step through it
        partition = next(partitions)
        # should round partition to nearest power of two
        self.assertEqual(partition.prefixlen(), 64)
        # should be a part of the partitioned prefix
        self.assertTrue(partition in prefix)
        # TODO: test for number of partitions?

    def test_suggest_range_valid(self):
        prefix = IP("10.0.0.0/8")
        prefixlen = 24
        n = 16
        suggested_ranges = suggest_range(prefix, prefixlen, n=n)
        self.assertEqual(len(suggested_ranges["candidates"]), 16)
        # make sure all suggestions are within bounds
        for suggested_range in suggested_ranges["candidates"]:
            self.assertTrue(suggested_range["prefix"] in prefix)

    def test_suggest_range_invalid(self):
        prefix = IP("10.0.0.0/24")
        prefixlen = 23
        candidates = suggest_range(prefix, prefixlen)["candidates"]
        # a too large range should only return the original prefix
        self.assertEqual(len(candidates), 1)
        self.assertEqual(IP(candidates[0]["prefix"]), prefix)

    # To test this function, we should really mock some prefixes, but for
    # simplicity reason, explicit dependency injection will do
    def test_get_available_subnets(self):
        base = ["10.0.0.0/8"]
        used = ["10.0.0.0/9"]
        available_subnets = _get_available_subnets(base, used)
        # sanity check: only 10.128.0.0/9 should be available
        self.assertTrue(IP("10.128.0.0/9") in IPSet(available_subnets))
        self.assertEqual(len(available_subnets), 1)
        self.assertEqual(available_subnets, sorted(available_subnets))
