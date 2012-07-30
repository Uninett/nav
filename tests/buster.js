var config = module.exports;

config["UnitTests"] = {
    rootPath:    "..",
    environment: "browser", // or "node"
    autoRun:     true,
    libs:        [
        "tests/require-config.js",
        "media/js/netmap/libs/jquery/jquery-full.js",
        "media/js/netmap/libs/require/require.js"
    ],
    sources:     [
        "media/js/netmap/**/*.js",
        "media/js/netmap/**/*.html",
        "media/js/netmap-extras.js"
    ],
    tests:       [
        "tests/unittests/**/*-test.js"
    ],
    extensions:  [
        require("buster-amd")
    ]
};
