define([
    'graph-utils',
    'jquery'], function (plugin) {
    describe("siNumbers", function () {
        it("should format two-digit numbers right", function() {
            assert.equal(plugin.siNumbers(42.0), "42.00");
        });

        it("should format milli-scale numbers right", function() {
            assert.equal(plugin.siNumbers(0.0042), "4.20 m");
        });

        it("should format micro-scale numbers right", function() {
            assert.equal(plugin.siNumbers(0.0000042), "4.20 µ");
        });

        it("should format nano-scale numbers right", function() {
            assert.equal(plugin.siNumbers(0.0000000042), "4.20 n");
        });

        it("should format pico-scale numbers right", function() {
            assert.equal(plugin.siNumbers(0.0000000000042), "4.20 p");
        });

        it("should format mega-scale numbers right", function() {
            assert.equal(plugin.siNumbers(42420000), "42.42 M");
        });

        it("should format giga-scale numbers right", function() {
            assert.equal(plugin.siNumbers(42420000000), "42.42 G");
        });

        it("should format tera-scale numbers right", function() {
            assert.equal(plugin.siNumbers(42420000000000), "42.42 T");
        });

        it("should format negative numbers right", function() {
            assert.equal(plugin.siNumbers(-0.0042), "-4.20 m");
        });

    });

    describe("parseSeriesMeta", function () {
        it("should return the name and no metadata when there is none", function () {
            assert.deepEqual(plugin.parseSeriesMeta("Total addresses"),
                {name: "Total addresses", meta: {}});
        });

        it("should parse a renderer", function () {
            assert.deepEqual(plugin.parseSeriesMeta("renderer=area;;10.0.0.0/24"),
                {name: "10.0.0.0/24", meta: {renderer: "area"}});
        });

        it("should parse a renderer and a colour", function () {
            assert.deepEqual(plugin.parseSeriesMeta("renderer=area;;color=#d9d9d9;;Unassigned"),
                {name: "Unassigned", meta: {renderer: "area", color: "#d9d9d9"}});
        });

        it("should keep equals signs in values", function () {
            assert.deepEqual(plugin.parseSeriesMeta("note=a=b;;name").meta, {note: "a=b"});
        });
    });

    describe("displayName", function () {
        it("should shorten a NAV metric path inside function calls to its last two parts", function () {
            const target = "scaleToSeconds(nonNegativeDerivative(nav.devices.gw_example_org.ports.ge-1_1_0.ifInErrors),1)";
            assert.equal(plugin.displayName(target), "ge-1_1_0.ifInErrors");
        });

        it("should keep a plain alias", function () {
            assert.equal(plugin.displayName("ge-1_1_0 ifInOctets"), "ge-1_1_0 ifInOctets");
        });
    });

    describe("toColumnar", function () {
        it("should return the timestamps and one column per series", function () {
            const data = [
                {target: "a", datapoints: [[1, 100], [2, 200]]},
                {target: "b", datapoints: [[3, 100], [4, 200]]}
            ];
            assert.deepEqual(plugin.toColumnar(data), [[100, 200], [1, 2], [3, 4]]);
        });

        it("should use the sorted union of timestamps, with null where a series has no value", function () {
            const data = [
                {target: "a", datapoints: [[1, 100], [3, 300]]},
                {target: "b", datapoints: [[4, 200], [5, 300]]}
            ];
            assert.deepEqual(plugin.toColumnar(data),
                [[100, 200, 300], [1, null, 3], [null, 4, 5]]);
        });

        it("should keep null values from Graphite", function () {
            const data = [{target: "a", datapoints: [[null, 100], [0, 200]]}];
            assert.deepEqual(plugin.toColumnar(data), [[100, 200], [null, 0]]);
        });

        it("should return an empty timestamp column for no series", function () {
            assert.deepEqual(plugin.toColumnar([]), [[]]);
        });
    });

    describe("withAlpha", function () {
        it("should convert #rrggbb to rgba", function () {
            assert.equal(plugin.withAlpha("#0072B2", 0.3), "rgba(0, 114, 178, 0.3)");
        });

        it("should convert #rgb to rgba", function () {
            assert.equal(plugin.withAlpha("#f00", 0.5), "rgba(255, 0, 0, 0.5)");
        });

        it("should return other colours unchanged", function () {
            assert.equal(plugin.withAlpha("steelblue", 0.3), "steelblue");
        });
    });

    describe("palette", function () {
        it("should contain eight hex colours", function () {
            assert.lengthOf(plugin.palette, 8);
            plugin.palette.forEach(color => assert.match(color, /^#[0-9A-F]{6}$/));
        });
    });
});
