var config = module.exports;

config["My tests"] = {
    rootPath: "../",
    environment: "browser", // or "node"
    libs: [
        "require.js",
        "jquery-1.4.4.min.js",
        "jquery.dataTables.min.js",
        "jquery-ui-1.8.21.custom.min.js"
    ],
    sources: [
        "src/info/*.js"
    ],
    tests: [
        "test/*/*-test.js"
    ],
    extensions: [
        require("buster-amd")
    ]
};
