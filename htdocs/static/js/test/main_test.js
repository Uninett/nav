var tests = [];
for (var file in window.__karma__.files) {
    if (/-test\.js$/.test(file)) {
        tests.push(file);
    }
}

require.baseUrl = '/base';
require.paths['testResources'] = 'test/resources';
require.deps = tests;
require.callback = window.__karma__.start;
requirejs(require);
