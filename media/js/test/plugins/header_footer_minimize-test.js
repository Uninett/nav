require(['plugins/header_footer_minimize',
    'resources/libs/text!testResources/plugins/header_footer_minimize/header.html',
    'libs/jquery'
], function (TestScript, headerEl, jquery) {
    buster.testCase("HeaderFooterMinimize:", {
        setUp: function () {
            this.script = new TestScript();
            this.script.initialize({
                header: headerEl,
                footer: headerEl
            });
        },
        "should minimize when header is showing": function () {
            var self = this;

            refute.equals(headerEl, "");
            self.script.toggleHeader();
            assert.equals(self.script.isHeaderShowing(), false);


        },
        "toggle a few times and make sure state is correct": function () {
            var self = this;
            assert.equals(self.script.isHeaderShowing(), true);
            self.script.toggleHeader();
            assert.equals(self.script.isHeaderShowing(), false);
        }
    });

});
