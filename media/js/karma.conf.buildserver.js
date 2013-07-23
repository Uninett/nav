var devConfig = require('./karma.conf.js');

module.exports = function (config) {
    var buildServerConfig = devConfig(config);

    buildServerConfig.set({
        coverageReporter: {
          type : 'cobertura',
          dir : 'coverage/'
        },
        browsers:      ['Chrome'],
        autoWatch:      false,
        singleRun: true
    });
};
