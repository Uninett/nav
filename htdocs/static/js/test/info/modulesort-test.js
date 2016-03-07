define([
    'dt_plugins/modulesort', 'libs/datatables.min'
], function (modulesort, DataTables) {
    describe("modulesort", function () {
        it("basic numeric sort should work", function () {
            var l = [2, 1];
            assert.deepEqual(l.sort(modulesort), [1, 2]);
        });
        it("basic text sorting should work", function () {
            var l = ['john', 'magne', 'bredal'];
            assert.deepEqual(l.sort(modulesort), ['bredal', 'john', 'magne']);
        });
        it("basic natural sort should work", function () {
            var l = ['Fa2/10', 'Fa2/2', 'Gi3/20', 'Gi3/1'];
            assert.deepEqual(l.sort(modulesort), ['Fa2/2', 'Fa2/10', 'Gi3/1', 'Gi3/20']);
        });
        it("should sort correctly on ifnames without prefix", function() {
            var l = ['5/10', '5/2', '3/20', '3/1', '4/1'];
            assert.deepEqual(l.sort(modulesort), ['3/1', '3/20', '4/1', '5/2', '5/10']);
        });
        it("should sort correctly on cisco interfaces", function() {
            var l = ['Fa5/10', 'Fa5/2', 'Gi3/20', 'Gi3/1', 'Te4/1'];
            assert.deepEqual(l.sort(modulesort), ['Gi3/1', 'Gi3/20', 'Te4/1', 'Fa5/2', 'Fa5/10']);
        });
        it("should sort correctly on mixed input", function() {
            var l = ['ge-3/0/0', 'ge-2/1/0', 'fxp0'];
            assert.deepEqual(l.sort(modulesort), ['fxp0', 'ge-2/1/0', 'ge-3/0/0']);
        });
        it("should sort correctly on other modules", function() {
            var l = ['ge-3/0/0', 'ge-1/1/0', 'ge-0/1/2'];
            assert.deepEqual(l.sort(modulesort), ['ge-0/1/2', 'ge-1/1/0','ge-3/0/0']);
        });
        it("should sort correctly on triple modules", function() {
            var l = ['Gi2/5/38', 'Gi2/2/44', 'Te1/3/8', 'Te1/2/2', 'Gi1/1/1'];
            assert.deepEqual(l.sort(modulesort), ['Gi1/1/1', 'Te1/2/2', 'Te1/3/8', 'Gi2/2/44', 'Gi2/5/38']);
        });
        it("should sort correctly on mixed modules", function() {
            var l = ['ge-0/0/0', 'em0', 'fxp0', 'bcm0', 'ge-1/0/9', 'ge-0/3/0'];
            assert.deepEqual(l.sort(modulesort), ['bcm0', 'em0', 'fxp0', 'ge-0/0/0', 'ge-0/3/0', 'ge-1/0/9']);
        });
        it("should sort correctly on input with spaces", function() {
            var l = ['ge-0/0/0', 'em0', '  fxp0 ', ' bcm0', 'ge-1/0/9   ', '    ge-0/3/0'];
            var j = [];
            var sorted = l.sort(modulesort);
            for (var i=0; i<sorted.length; i++) {
                j.push($.trim(sorted[i]));
            }
            assert.deepEqual(j, ['bcm0', 'em0', 'fxp0', 'ge-0/0/0', 'ge-0/3/0', 'ge-1/0/9']);
        });
        it("should sort correctly on input inside links", function() {
            var l = [
                '<a href="/ipdevinfo/trd-gw1.uninett.no/interface=337/"> ge-0/2/0 </a>',
                '<a href="/ipdevinfo/trd-gw1.uninett.no/interface=395/"> ge-0/0/0 </a>',
                '<a href="/ipdevinfo/trd-gw1.uninett.no/interface=383/"> em0 </a>',
                '<a href="/ipdevinfo/trd-gw1.uninett.no/interface=367/"> fxp0 </a>',
                '<a href="/ipdevinfo/trd-gw1.uninett.no/interface=355/"> bcm0 </a>',
                '<a href="/ipdevinfo/trd-gw1.uninett.no/interface=361/"> ge-1/1/0 </a>'
                ];
            var j = [
                '<a href="/ipdevinfo/trd-gw1.uninett.no/interface=355/"> bcm0 </a>',
                '<a href="/ipdevinfo/trd-gw1.uninett.no/interface=383/"> em0 </a>',
                '<a href="/ipdevinfo/trd-gw1.uninett.no/interface=367/"> fxp0 </a>',
                '<a href="/ipdevinfo/trd-gw1.uninett.no/interface=395/"> ge-0/0/0 </a>',
                '<a href="/ipdevinfo/trd-gw1.uninett.no/interface=337/"> ge-0/2/0 </a>',
                '<a href="/ipdevinfo/trd-gw1.uninett.no/interface=361/"> ge-1/1/0 </a>'
                ];

            assert.deepEqual(l.sort(modulesort), j);
        });
        describe("module-asc", function () {
            it("should be appended to jquery datatable", function () {
                assert.isFunction(DataTables.ext.oSort['module-asc']);
            });
            it("should sort modules ascending", function () {
                var l = [1, 2];
                assert.deepEqual(
                    l.sort(DataTables.ext.oSort['module-asc']),
                    [1, 2]
                );
            });
        });
        describe("module-desc", function () {
            it("should be appended to jquery datatable", function () {
                assert.isFunction(DataTables.ext.oSort['module-desc']);
            });
            it("should sort modules ascending", function () {
                var l = [1, 2];
                assert.deepEqual(
                    l.sort(DataTables.ext.oSort['module-desc']),
                    [2, 1]
                );
            });
        });

    });
});
