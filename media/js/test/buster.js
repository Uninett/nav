var config = module.exports;

config["My tests"] = {
    rootPath: "../",
    environment: "browser", // or "node"
    libs: [
        "jquery-1.4.4.min.js",
        "jquery.dataTables.min.js",
        "jquery-ui-1.8.21.custom.min.js",
    	"require.js"
    ],
    sources: [
	"info/*"
    ],
    tests: [
	"test/*/*-test.js"
    ],
    extensions: [
        require("buster-amd")
    ]
};
