require([

    // Load our app module and pass it to our definition function
    'netmap/app'

], function (App) {
    document.navNetmapAppSpinner.stop(); // global spinner while javascript is loading it's dependencies
    define.amd.jQuery = true;

    // The "app" dependency is passed in as "App"
    // Again, the other dependencies passed in are not "AMD" therefore don't pass a parameter to this function
    App.initialize();
}, function (errorCallback) {
    if (errorCallback.requireType === 'timeout') {
        alert("Timed out while loading resources for javascript application, please try to reload the page!");
    } else {
        throw errorCallback;
    }
});
