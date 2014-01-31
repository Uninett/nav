define(["netmap/models/node", "netmap/views/widgets/netbox_info", "libs/jquery"], function (Node, View) {

    // Skipping these tests as they produce warnings about missing images for each test run.
    // Either find a way to ignore only missing images or better yet - make tests that do not rely on html with images
    describe.skip("View tests", function () {
        beforeEach(function (done) {
            var node = new Node({
                category: "GW",
                id: "335",
                ip: "192.168.42.1",
                ipdevinfo_link: "/ipdevinfo/nav-gw.uninett.no/",
                position: null,
                sysname: "nav-gw.uninett.no",
                up: "y",
                up_image: "green.png"
            });

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
