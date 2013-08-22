var tests = [];
for (var file in window.__karma__.files) {
    if (/-test\.js$/.test(file)) {
        tests.push(file);
    }
}

//console.log(tests);

require.deps = tests;
require.callback = window.__karma__.start;
requirejs(require);