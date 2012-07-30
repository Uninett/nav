define(["NetmapExtras"], function (NetmapExtras) {

    buster.testCase("Traffic SI units tests", {
        setUp: function () {
            this.extras = NetmapExtras;
        },

        "Bits to Tbps":                  function () {
            assert.equals(this.extras.convert_bits_to_si(1000 * 1000 * 1000 * 1000 * 99999), "99999Tbps");
            assert.equals(this.extras.convert_bits_to_si(1000 * 1000 * 1000 * 1000), "1Tbps");
            assert.equals(this.extras.convert_bits_to_si(1000 * 1000 * 1000 * 999), "999Gbps");
        },
        "Bits to Gbps":                  function () {
            "use strict";
            assert.equals(this.extras.convert_bits_to_si(1000 * 1000 * 1000 * 999), "999Gbps");
            assert.equals(this.extras.convert_bits_to_si(1000 * 1000 * 1000), "1Gbps");
            assert.equals(this.extras.convert_bits_to_si(1000 * 1000 * 999), "999Mbps");
        },
        "Bits to Mbps":                  function () {
            "use strict";
            assert.equals(this.extras.convert_bits_to_si(1000 * 1000 * 999), "999Mbps");
            assert.equals(this.extras.convert_bits_to_si(1000 * 1000), "1Mbps");
            assert.equals(this.extras.convert_bits_to_si(1000 * 999), "999Kbps");
        },
        "Bits to Kbps":                  function () {
            "use strict";
            assert.equals(this.extras.convert_bits_to_si(1000 * 999), "999Kbps");
            assert.equals(this.extras.convert_bits_to_si(1000), "1Kbps");
        },
        "Bits to actually just be bits": function () {
            "use strict";
            assert.equals(this.extras.convert_bits_to_si(999), "999bps");
        },
        "// Deal with math round to low": function () {
            "use strict";
            assert.equals(this.extras.convert_bits_to_si(1000 * 1000 * 1000 * 999.99), "1Tbps");
        }
    });

    buster.testCase("Traffic IEC units tests", {
        setUp:                        function () {
            "use strict";
            this.extras = NetmapExtras;
        },
        "Bits to Tebibits pr second": function () {
            "use strict";
            assert.equals(this.extras.convert_bits_to_iec(1024 * 1024 * 1024 * 1025), "1Tib/s");
            assert.equals(this.extras.convert_bits_to_iec(1024 * 1024 * 1024 * 1024), "1Tib/s");
            assert.equals(this.extras.convert_bits_to_iec(1024 * 1024 * 1024 * 1023), "1023Gib/s");
        },
        "Bits to Gibibits pr second": function () {
            "use strict";
            assert.equals(this.extras.convert_bits_to_iec(1024 * 1024 * 1025), "1Gib/s");
            assert.equals(this.extras.convert_bits_to_iec(1024 * 1024 * 1024), "1Gib/s");
            assert.equals(this.extras.convert_bits_to_iec(1024 * 1024 * 1023), "1023Mib/s");
        },
        "Bits to Mibibits pr second": function () {
            "use strict";
            assert.equals(this.extras.convert_bits_to_iec(1024 * 1025), "1Mib/s");
            assert.equals(this.extras.convert_bits_to_iec(1024 * 1024), "1Mib/s");
            assert.equals(this.extras.convert_bits_to_iec(1024 * 1023), "1023Kib/s");
        },
        "Bits to Kibibits pr second": function () {
            "use strict";
            assert.equals(this.extras.convert_bits_to_iec(1025), "1Kib/s");
            assert.equals(this.extras.convert_bits_to_iec(1024), "1Kib/s");
            assert.equals(this.extras.convert_bits_to_iec(1023), "1023b/s");
        }
    });
});
/*buster.testCase("speed translations :: SI units", {
 "bits to Tbps": function () {

 assert(true);
 }
 });
 asd
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
 }*/
