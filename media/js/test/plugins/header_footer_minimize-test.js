require(['plugins/header_footer_minimize',
    'resources/libs/text!testResources/plugins/header_footer_minimize/header.html',
    'libs/jquery'
], function (TestScript, headerEl) {
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
        },
        "toggle a few times by using hotkey": function () {
            this.script = new TestScript();
            this.script.initialize( {
                header: { el: headerEl, hotkey: { altKey: true, ctrlKey: true, charCode: 102} },
                footer: { el: headerEl, hotkey: { altKey: true, ctrlKey: true, charCode: 102} }
            });

            var e = $.Event("keypress");
            e.charCode = e.which = 102;
            e.altKey = true;
            e.ctrlKey = true;

            assert.equals(this.script.isHeaderShowing(), true);

            $(document).trigger(e);

            assert.equals(this.script.isHeaderShowing(), false);

            $(document).trigger(e);

            assert.equals(this.script.isHeaderShowing(), true);

        },
        "do not react on not bound hotkey, but only bound hotkey": function () {
            this.script = new TestScript();
            this.script.initialize( {
                header: { el: headerEl, hotkey: { altKey: true, ctrlKey: true, charCode: 102} },
                footer: { el: headerEl, hotkey: { altKey: true, ctrlKey: true, charCode: 102} }
            });

            var e = $.Event("keypress");
            e.charCode = e.which = 102;
            e.altKey = true;
            e.ctrlKey = true;

            assert.equals(this.script.isHeaderShowing(), true);

            $(document).trigger(e);
            assert.equals(this.script.isHeaderShowing(), false);

            var noActionEvent = $.Event("keypress");
            noActionEvent.charCode = noActionEvent.which = 102;
            noActionEvent.altkey = false;
            noActionEvent.ctrlKey = false;

            $(document).trigger(noActionEvent);
            assert.equals(this.script.isHeaderShowing(), false);

            $(document).trigger(e);

            assert.equals(this.script.isHeaderShowing(), true);
        }
    });

});
