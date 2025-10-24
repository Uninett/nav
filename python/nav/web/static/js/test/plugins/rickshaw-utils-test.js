define([
    'rickshaw-utils',
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
});
