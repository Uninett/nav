var config = module.exports;

config["My tests"] = {
    rootPath: "../",
    environment: "browser", // or "node"
    libs: [
        "require_config.js",
        "require_config.*.js",
        "libs/require.js",
        "libs/underscore.js",
        "libs/backbone.js",
        "libs/*.js"
    ],
    resources: [
        "resources/**/*.js",
        "resources/**/*.html",
        "test/resources/**/*.html",
        "src/**/*.js",
        "src/**/*.html"
    ],
    tests: [
        "test/*/*-test.js"
    ],
    extensions: [
        require("buster-amd")
    ]
};
