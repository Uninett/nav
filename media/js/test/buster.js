var config = module.exports;

config["My tests"] = {
    rootPath: "../",
    environment: "browser", // or "node"
    libs: [
        "require_config.js",
        "require_testconfig.js",
        "libs/*.js"
    ],
    resources: [
        "src/*/*.js"
    ],
    tests: [
        "test/*/*-test.js"
    ],
    extensions: [
        require("buster-amd")
    ]
};
