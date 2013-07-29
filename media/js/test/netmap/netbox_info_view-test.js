define(["netmap/views/widgets/netbox_info", "libs/jquery"], function (View) {

    describe("View tests", function () {
        beforeEach(function (done) {
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
            assert.isNotNull(this.netbox_info_view.node, "Node should not be null!");
            done();
        });

        it("Hostname listed in header section of netbox_info view", function () {
            var dom = this.netbox_info_view.render().el;
            assert.strictEqual($('.node_sysname', dom).text(), "nav-gw.uninett.no");
        });

        it("IPdevinfo listed in properties of netbox", function () {
            var dom = this.netbox_info_view.render().el;
            assert.strictEqual(($('.node_sysname a', dom).attr('href')), "/ipdevinfo/nav-gw.uninett.no/");
        });
    });
});
