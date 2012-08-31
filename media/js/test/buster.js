var config = module.exports;

config["My tests"] = {
    rootPath: "../",
    environment: "browser", // or "node"
    libs: [
        "libs/require.js",
        "libs/jquery.js",
        "libs/jquery.dataTables.min.js",
        "libs/jquery-ui-1.8.21.custom.min.js"
    ],
    sources: [
        "src/info/*.js",
        "src/plugins/*.js",
        "src/dt_plugins/*.js"
    ],
    tests: [
        "test/*/*-test.js"
    ],
    extensions: [
        require("buster-amd")
    ]
};
