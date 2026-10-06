/*
 * chartjs-plugin-zoom requires the module "hammerjs", which it only uses for
 * pinch-to-zoom and panning on touch screens. NAV uses neither, so this stub
 * stands in for Hammer.js. The plugin skips its gesture support when the
 * module is undefined. require_config.js maps "hammerjs" to this module.
 */
define(() => undefined);
