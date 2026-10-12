define(['underscore'], function (_) {
    'use strict';

    // Backbone 1.0.0 and libs/backbone-eventbroker.js predate AMD and read
    // a bare global `_`. The vendored underscore build only sets window._
    // when no AMD loader is present, which is never the case under
    // RequireJS. Set it explicitly so the shimmed Backbone can find it.
    window._ = _;

    return _;
});
