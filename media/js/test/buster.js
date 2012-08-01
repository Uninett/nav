var config = module.exports;

config["My tests"] = {
    rootPath: "../",
    environment: "browser", // or "node"
    sources: [
        "jquery-1.4.4.min.js",
        "jquery.dataTables.min.js",
        "jquery-ui-1.8.21.custom.min.js",
        "info.js",
    ],
    tests: [
        "test/*-test.js"
    ]
}
