var require = {
    baseUrl: '/js',
    waitSeconds: 7, // default
    paths: {
        "libs": "libs",
        "plugins": "src/plugins",
        "dt_plugins": "src/dt_plugins",
        "info": "src/info",
        "netmap": "src/netmap"
    },
    shim: {
        'libs/jquery-ui-1.8.21.custom.min': ['libs/jquery'],
        'libs/jquery.dataTables.min': ['libs/jquery'],
        'libs/downloadify.min': ['libs/jquery', 'libs/swfobject'],
        'libs/spin.min': ['libs/jquery'],
        'libs/underscore': {
            exports: '_'
        },
        'libs/backbone': ["libs/underscore", "libs/jquery"],
        'libs/backbone-eventbroker': ['libs/backbone']

    },
    urlArgs: "nav=" + (new Date()).getTime()
};
