from nav import util
from nav.web.machinetracker.utils import get_prefix_info

class MachinetrackerIPRange(util.IPRange):

    @classmethod
    def get_mask_for_network(cls, network):
        """ Lookup prefix from NAV database """
        prefix = get_prefix_info(network)
        prefix_address = prefix.net_address
        prefix_cidr = prefix_address.split("/")
        return prefix_cidr[1]



