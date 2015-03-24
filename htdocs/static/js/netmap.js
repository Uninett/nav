var TRAFFIC_META = {
    'tib': 1099511627776,
    'gib': 1073741824,
    'mib': 1048576,
    'kib': 1024,
    'tb':  1000000000000,
    'gb':  1000000000,
    'mb':  1000000,
    'kb':  1000
};


// SI Units, http://en.wikipedia.org/wiki/SI_prefix
function convert_bits_to_si(bits) {
    if (bits >= TRAFFIC_META.tb) {
        return '{0}Tbps'.format(Math.round(((bits / TRAFFIC_META.tb) * 100) / 100));
    } else if (bits >= TRAFFIC_META.gb) {
        return '{0}Gbps'.format(Math.round(((bits / TRAFFIC_META.gb) * 100) / 100));
    } else if (bits >= TRAFFIC_META.mb) {
        return '{0}Mbps'.format(Math.round(((bits / TRAFFIC_META.mb) * 100) / 100));
    } else if (bits >= TRAFFIC_META.kb) {
        return '{0}Kbps'.format(Math.round(((bits / TRAFFIC_META.kb) * 100) / 100));
    }

    return '{0}b/s'.format(Math.round((bits * 100) / 100));
}


String.prototype.format = function () {
    var args = arguments;
    return this.replace(/\{(\d+)\}/g, function (match, number) {
        return typeof args[number] !== 'undefined' ? args[number] : match;

    });
};
