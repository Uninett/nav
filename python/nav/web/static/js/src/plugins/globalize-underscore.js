define(['underscore'], function (_) {
    'use strict';

    // The vendored underscore build only assigns window._ when no AMD
    // loader is present. RequireJS always defines one, so the build takes
    // that branch and never touches the global -- but old, non-AMD-aware
    // scripts (Backbone, Marionette) read `_` as a bare global. Force it.
    window._ = _;

    return _;
});
