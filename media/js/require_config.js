var require = {
    baseUrl: '/js',
    paths: {
        "libs": "libs",
        "plugins": "src/plugins",
        "dt_plugins": "src/dt_plugins",
        "info": "src/info"
    },
    shim: {
        'libs/jquery-ui-1.8.21.custom.min': ['libs/jquery'],
        'libs/jquery.dataTables.min': ['libs/jquery'],
        'libs/downloadify.min': ['libs/jquery', 'libs/swfobject']
    }
};