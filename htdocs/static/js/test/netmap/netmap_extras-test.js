define(["plugins/netmap-extras"], function (NetmapExtras) {
    describe("Traffic SI units tests", function () {
        beforeEach(function () {
            this.extras = NetmapExtras;
        });

        it("Bits to Tbps",                  function () {
            assert.strictEqual(this.extras.convert_bits_to_si(1000 * 1000 * 1000 * 1000 * 99999), "99999Tbps");
            assert.strictEqual(this.extras.convert_bits_to_si(1000 * 1000 * 1000 * 1000), "1Tbps");
            assert.strictEqual(this.extras.convert_bits_to_si(1000 * 1000 * 1000 * 999), "999Gbps");
        });
        it("Bits to Gbps",                  function () {
            assert.strictEqual(this.extras.convert_bits_to_si(1000 * 1000 * 1000 * 999), "999Gbps");
            assert.strictEqual(this.extras.convert_bits_to_si(1000 * 1000 * 1000), "1Gbps");
            assert.strictEqual(this.extras.convert_bits_to_si(1000 * 1000 * 999), "999Mbps");
        });
        it("Bits to Mbps",                  function () {
            assert.strictEqual(this.extras.convert_bits_to_si(1000 * 1000 * 999), "999Mbps");
            assert.strictEqual(this.extras.convert_bits_to_si(1000 * 1000), "1Mbps");
            assert.strictEqual(this.extras.convert_bits_to_si(1000 * 999), "999Kbps");
        });
        it("Bits to Kbps",                  function () {
            assert.strictEqual(this.extras.convert_bits_to_si(1000 * 999), "999Kbps");
            assert.strictEqual(this.extras.convert_bits_to_si(1000), "1Kbps");
        });
        it("Bits to actually just be bits", function () {
            assert.strictEqual(this.extras.convert_bits_to_si(999), "999bps");
        });

        it.skip("Deal with math round to low", function () {
            assert.strictEqual(this.extras.convert_bits_to_si(1000 * 1000 * 1000 * 999.999), "1Tbps");
        });
    });

    describe("Traffic IEC units tests", function () {
        beforeEach(                       function () {
            this.extras = NetmapExtras;
        });
        it("Bits to Tebibits pr second", function () {
            assert.strictEqual(this.extras.convert_bits_to_iec(1024 * 1024 * 1024 * 1025), "1Tib/s");
            assert.strictEqual(this.extras.convert_bits_to_iec(1024 * 1024 * 1024 * 1024), "1Tib/s");
            assert.strictEqual(this.extras.convert_bits_to_iec(1024 * 1024 * 1024 * 1023), "1023Gib/s");
        });
        it("Bits to Gibibits pr second", function () {
            assert.strictEqual(this.extras.convert_bits_to_iec(1024 * 1024 * 1025), "1Gib/s");
            assert.strictEqual(this.extras.convert_bits_to_iec(1024 * 1024 * 1024), "1Gib/s");
            assert.strictEqual(this.extras.convert_bits_to_iec(1024 * 1024 * 1023), "1023Mib/s");
        });
        it("Bits to Mibibits pr second", function () {
            assert.strictEqual(this.extras.convert_bits_to_iec(1024 * 1025), "1Mib/s");
            assert.strictEqual(this.extras.convert_bits_to_iec(1024 * 1024), "1Mib/s");
            assert.strictEqual(this.extras.convert_bits_to_iec(1024 * 1023), "1023Kib/s");
        });
        it("Bits to Kibibits pr second", function () {
            assert.strictEqual(this.extras.convert_bits_to_iec(1025), "1Kib/s");
            assert.strictEqual(this.extras.convert_bits_to_iec(1024), "1Kib/s");
            assert.strictEqual(this.extras.convert_bits_to_iec(1023), "1023b/s");
        });
    });
});