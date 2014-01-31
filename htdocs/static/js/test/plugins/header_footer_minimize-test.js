define(['plugins/header_footer_minimize',
    'libs-amd/text!testResources/plugins/header_footer_minimize/header.html',
    'libs/jquery'
], function (TestScript, headerEl) {
        var script;
        describe("HeaderFooterMinimize:", function () {

            beforeEach(function () {
                if (script) {
                    script.close();
                    script = undefined;
                }
                script = new TestScript();
                script.initialize({
                    header: headerEl,
                    footer: headerEl
                });
            });

            it("should minimize when header is showing", function () {
                assert.notEqual(headerEl, "");
                script.toggleHeader();
                assert.strictEqual(script.isHeaderShowing(), false);
            });

            it("toggle a few times and make sure state is correct", function () {
                assert.strictEqual(script.isHeaderShowing(), true);
                script.toggleHeader();
                assert.strictEqual(script.isHeaderShowing(), false);
            });
            it("toggle a few times by using hotkey", function () {
                script = new TestScript();
                script.initialize({
                    header: { el: headerEl, hotkey: { altKey: true, ctrlKey: true, charCode: 102} },
                    footer: { el: headerEl, hotkey: { altKey: true, ctrlKey: true, charCode: 102} }
                });

                var e = $.Event("keypress");
                e.charCode = e.which = 102;
                e.altKey = true;
                e.ctrlKey = true;

                assert.strictEqual(script.isHeaderShowing(), true);

                $(document).trigger(e);

                assert.strictEqual(script.isHeaderShowing(), false);

                $(document).trigger(e);

                assert.strictEqual(script.isHeaderShowing(), true);
            });
            it("do not react on not bound hotkey, but only bound hotkey", function () {
                script = new TestScript();
                script.initialize({
                    header: { el: headerEl, hotkey: { altKey: true, ctrlKey: true, charCode: 102} },
                    footer: { el: headerEl, hotkey: { altKey: true, ctrlKey: true, charCode: 102} }
                });

                var e = $.Event("keypress");
                e.charCode = e.which = 102;
                e.altKey = true;
                e.ctrlKey = true;

                assert.strictEqual(script.isHeaderShowing(), true);

                $(document).trigger(e);
                assert.strictEqual(script.isHeaderShowing(), false);

                var noActionEvent = $.Event("keypress");
                noActionEvent.charCode = noActionEvent.which = 102;
                noActionEvent.altkey = false;
                noActionEvent.ctrlKey = false;

                $(document).trigger(noActionEvent);
                assert.strictEqual(script.isHeaderShowing(), false);

                $(document).trigger(e);

                assert.strictEqual(script.isHeaderShowing(), true);
            });

        });
});
