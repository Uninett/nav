module.exports = function (config) {
    config.set({
        // base path, that will be used to resolve files and exclude
        basePath:       '..',


        // frameworks to use
        frameworks:     ['mocha', 'requirejs', 'chai'],

        // list of files / patterns to load in the browser
        files:          [
            'require_config.js',
            'libs/jquery-3.7.1.min.js',
            {pattern: 'libs/**/*.js', included: false},
            {pattern: 'src/**/*.js', included: false},
            {pattern: 'src/**/*.html', included: false},
            {pattern: 'resources/**/*.js', included: false},
            {pattern: 'test/resources/**/*.html', included: false},
            'test/main_test.js',
            {pattern: 'test/**/*.js', included: false}
        ],


        // list of files to exclude
        exclude:        [

        ],

        preprocessors: {
                       'src/**/*.js': 'coverage'
        },


        // test results reporter to use
        // possible values: 'dots', 'progress', 'junit', 'growl', 'coverage'
        reporters:      ['dots', 'coverage'],

        coverageReporter: {
          type : 'html',
          dir : 'coverage/'
        },
        junitReporter: {
          outputFile: 'javascript-results.xml',
          suite: ''
        },


        // web server port
        port:           9876,


        // cli runner port
        runnerPort:     9100,


        // enable / disable colors in the output (reporters and logs)
        colors:         true,


        // level of logging
        // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
        logLevel:       config.LOG_INFO,


        // enable / disable watching file and executing tests whenever any file changes
        autoWatch:      true,


        // Start these browsers, currently available:
        // - Chrome
        // - ChromeCanary
        // - Firefox
        // - Opera
        // - Safari (only Mac)
        // - PhantomJS
        // - IE (only Windows)
        browsers:       ['Chrome', 'Firefox', 'PhantomJS'],


        // If browser does not capture in given timeout [ms], kill it
        captureTimeout: 60000,


        // Continuous Integration mode
        // if true, it capture browsers, run tests and exit
        singleRun:      false
    });
    return config;
};
