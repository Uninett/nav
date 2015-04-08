/**
 * How to use this file - or "We finally required node as a dependency so we
 * could optimize page loading".
 *
 * Why optimize? Because it makes the pages load faster. By a lot.
 *
 * The base url in require_config.js must be set to '/static/js/prod' or
 * whereever the browser looks for the js-files. It's totally ok to optimize and
 * then copy.
 * 
 * Command to run: r.js -o build.js
 *
 * All files defined in the modules directive below are now available in 'prod'
 * directory. 
 *
 * NB: When I tested this, we had a base file called 'main' for all pages, and
 * individual files for every page. This may lead to problems if a library is
 * required by both the main and the individual script. jQuery for instance is a
 * problem. So you need to make sure jQuery is only required once, which means
 * removing all shims and all individual requires for jQuery, and then make sure
 * only main requires it. This may be the case with other libs in 'main' aswell.
 */

({
    baseUrl: '.',
    mainConfigFile: 'require_config.js',
    skipDirOptimize: true,
    optimizeCss: 'none',
    dir: 'prod',
    modules: [
        { name: 'src/main' },
        { name: 'src/webfront' },
        { name: 'src/maintenance' },
        { name: 'src/status2/status' },
        { name: 'src/seeddb' },
        { name: 'src/netmap/netmap' },
        { name: 'src/networkexplorer' },
    ]
});
