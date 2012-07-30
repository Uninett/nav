//var buster = require("buster");

define(["jQuery", "netmap/views/netbox_info"], function ($, View) {


    buster.testCase("View tests", {
        setUp: function (done) {
            var node = {
                data:   {
                    category:       "GW",
                    id:             "335",
                    ip:             "192.168.42.1",
                    ipdevinfo_link: "/ipdevinfo/nav-gw.uninett.no/",
                    position:       null,
                    sysname:        "nav-gw.uninett.no",
                    up:             "y",
                    up_image:       "green.png"
                },
                fixed:  true,
                group:  0,
                index:  138,
                name:   "nav-gw",
                px:     1028.0180065733132,
                py:     1891.7714585731676,
                weight: 4,
                x:      1028.0180065733132,
                y:      1891.7714585731676
            };
            this.netbox_info_view = new View();
            this.netbox_info_view.node = node;
            refute.isNull(this.netbox_info_view.node, "Node should not be null!");
            done();
        },

        "Hostname listed in header section of netbox_info view": function () {
            var dom = this.netbox_info_view.render().el;
            assert.equals($('h2', dom).html(), "nav-gw.uninett.no");
        },
        "IPdevinfo listed in properties of netbobx": function () {
            "use strict";
            var dom = this.netbox_info_view.render().el;
            assert.equals($('ul.netmap-node-menu li:first a', dom).attr('href'), "/ipdevinfo/nav-gw.uninett.no/");
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
