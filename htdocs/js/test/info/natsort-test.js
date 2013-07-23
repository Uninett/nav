define([
    'dt_plugins/natsort', 'libs/jquery', 'libs/jquery.dataTables.min'
], function (natsort) {
    describe("natsort", function () {
        it("basic numeric sort should work", function () {
            var l = [2, 1];
            assert.deepEqual(l.sort(natsort), [1, 2]);
        });
        it("basic text sorting should work", function () {
            var l = ['john', 'magne', 'bredal'];
            assert.deepEqual(l.sort(natsort), ['bredal', 'john', 'magne']);
        });
        it("basic natural sort should work", function () {
            var l = ['Fa2/10', 'Fa2/2', 'Gi3/20', 'Gi3/1'];
            assert.deepEqual(l.sort(natsort), ['Fa2/2', 'Fa2/10', 'Gi3/1', 'Gi3/20']);
        });
        it("should sort correctly on ifnames without prefix", function() {
            var l = ['5/10', '5/2', '3/20', '3/1', '4/1'];
            assert.deepEqual(l.sort(natsort), ['3/1', '3/20', '4/1', '5/2', '5/10']);
        });
        it("should sort correctly on mixed input", function() {
            var l = ['ge-3/0/0', 'ge-2/1/0', 'fxp0'];
            assert.deepEqual(l.sort(natsort), ['fxp0', 'ge-2/1/0', 'ge-3/0/0']);
        });
        it("should sort correctly on other modules", function() {
            var l = ['ge-3/0/0', 'ge-1/1/0', 'ge-0/1/2'];
            assert.deepEqual(l.sort(natsort), ['ge-0/1/2', 'ge-1/1/0','ge-3/0/0']);
        });
        it("should sort correctly on triple modules", function() {
            var l = ['2/5/3', '2/2/4', '1/3/8', '1/2/2', '1/1/1'];
            assert.deepEqual(l.sort(natsort), ['1/1/1', '1/2/2', '1/3/8', '2/2/4', '2/5/3']);
        });
    });
});
