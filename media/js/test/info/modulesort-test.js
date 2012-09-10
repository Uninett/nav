require([
    'dt_plugins/modulesort', 'libs/jquery', 'libs/jquery.dataTables.min'
], function (modulesort) {
    buster.testCase("modulesort", {
        "basic numeric sort should work": function () {
            var l = [2, 1];
            assert.equals(l.sort(modulesort.moduleSort), [1, 2]);
        },
        "basic text sorting should work": function () {
            var l = ['john', 'magne', 'bredal'];
            assert.equals(l.sort(modulesort.moduleSort), ['bredal', 'john', 'magne']);
        },
        "basic natural sort should work": function () {
            var l = ['Fa2/10', 'Fa2/2', 'Gi3/20', 'Gi3/1'];
            assert.equals(l.sort(modulesort.moduleSort), ['Fa2/2', 'Fa2/10', 'Gi3/1', 'Gi3/20']);
        },
        "should sort correctly on ifnames without prefix": function() {
            var l = ['5/10', '5/2', '3/20', '3/1', '4/1'];
            assert.equals(l.sort(modulesort.moduleSort), ['3/1', '3/20', '4/1', '5/2', '5/10']);
        },
        "should sort correctly on cisco interfaces": function() {
            var l = ['Fa5/10', 'Fa5/2', 'Gi3/20', 'Gi3/1', 'Te4/1'];
            assert.equals(l.sort(modulesort.moduleSort), ['Gi3/1', 'Gi3/20', 'Te4/1', 'Fa5/2', 'Fa5/10']);
        },
        "should sort correctly on mixed input": function() {
            var l = ['ge-3/0/0', 'ge-2/1/0', 'fxp0'];
            assert.equals(l.sort(modulesort.moduleSort), ['fxp0', 'ge-2/1/0', 'ge-3/0/0']);
        },
        "should sort correctly on other modules": function() {
            var l = ['ge-3/0/0', 'ge-1/1/0', 'ge-0/1/2'];
            assert.equals(l.sort(modulesort.moduleSort), ['ge-0/1/2', 'ge-1/1/0','ge-3/0/0']);
        }
    });
});
