define(function () {


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

    String.prototype.format = function () {
        var args = arguments;
        return this.replace(/\{(\d+)\}/g, function (match, number) {
            return typeof args[number] !== 'undefined' ? args[number] : match;

        });
    };

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
        }

    };

    _this = publicMethods;
    return _this;
});

