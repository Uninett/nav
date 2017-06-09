var devConfig = require('./karma.conf.js');

module.exports = function (config) {
    var buildServerConfig = devConfig(config);

    buildServerConfig.set({
        reporters: ['dots', 'coverage', 'junit'],
        coverageReporter: {
          type : 'cobertura',
          dir : 'coverage/'
        },
        browsers:      ['ChromeNoSandbox', 'Firefox', 'PhantomJS'],
        autoWatch:      false,
        singleRun: true,
        colors: false,

        customLaunchers: {
            ChromeNoSandbox: {
                base: 'Chrome',
                flags: ['--no-sandbox']
            }
        }
    });
};
