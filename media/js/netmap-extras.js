define([], function () {

    var _this; // proxy variable

    var _TRAFFIC_META = {
        'tib': 1099511627776,
        'gib': 1073741824,
        'mib': 1048576,
        'kib': 1024,
        'tb':  1000000000000,
        'gb':  1000000000,
        'mb':  1000000,
        'kb':  1000
    };
    var _TOPOLOGIES = {
        1: 'Layer 2',
        2: 'Layer 2 with VLAN',
        3: 'Layer 3'
    };

    var _LINKS_TOPOLOGIES = {
        1: 'layer2',
        2: 'layer2vlan',
        3: 'layer3'
    };

    // http://stackoverflow.com/questions/1970175/getting-json-key-from-value-or-inverting-json-data
    function swapJsonKeyValues(input) {
        var one, output = {};
        for (one in input) {
            if (input.hasOwnProperty(one)) {
                output[input[one]] = one;
            }
        }
        return output;
    }
    var _LINKS_TOPOLOGIES_REVERSE = swapJsonKeyValues(_LINKS_TOPOLOGIES);

    var publicMethods = {
        // SI Units, http://en.wikipedia.org/wiki/SI_prefix
        convert_bits_to_si: function (bits) {
            if (bits >= _TRAFFIC_META.tb) {
                return '{0}Tbps'.format(Math.round(((bits / _TRAFFIC_META.tb) * 100) / 100));
            } else if (bits >= _TRAFFIC_META.gb) {
                return '{0}Gbps'.format(Math.round(((bits / _TRAFFIC_META.gb) * 100) / 100));
            } else if (bits >= _TRAFFIC_META.mb) {
                return '{0}Mbps'.format(Math.round(((bits / _TRAFFIC_META.mb) * 100) / 100));
            } else if (bits >= _TRAFFIC_META.kb) {
                return '{0}Kbps'.format(Math.round(((bits / _TRAFFIC_META.kb) * 100) / 100));
            }

            return '{0}bps'.format(Math.round((bits * 100) / 100));
        },
        // IEC binary units: http://en.wikipedia.org/wiki/Kibibyte
        convert_bits_to_iec: function (bits) {
            if (bits >= _TRAFFIC_META.tib) {
                return '{0}Tib/s'.format(Math.round(((bits / _TRAFFIC_META.tib) * 100) / 100));
            } else if (bits >= _TRAFFIC_META.gib) {
                return '{0}Gib/s'.format(Math.round(((bits / _TRAFFIC_META.gib) * 100) / 100));
            } else if (bits >= _TRAFFIC_META.mib) {
                return '{0}Mib/s'.format(Math.round(((bits / _TRAFFIC_META.mib) * 100) / 100));
            } else if (bits >= _TRAFFIC_META.kib) {
                return '{0}Kib/s'.format(Math.round(((bits / _TRAFFIC_META.kib) * 100) / 100));
            }

            return '{0}b/s'.format(Math.round((bits * 100) / 100));
        },
        topology_id_to_topology_link: function (topology_id) {
            return _LINKS_TOPOLOGIES[topology_id];
        },
        topology_link_to_id: function (topology_link) {
            return _LINKS_TOPOLOGIES_REVERSE[topology_link];
        }

    };

    _this = publicMethods;
    return publicMethods;
});

String.prototype.format = function () {
    var args = arguments;
    return this.replace(/\{(\d+)\}/g, function (match, number) {
        return typeof args[number] !== 'undefined' ? args[number] : match;

    });
};