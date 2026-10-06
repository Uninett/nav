/*
 * chartjs-plugin-zoom requires the module "chart.js/helpers". The Chart.js
 * UMD build has no such module, but exposes the same functions as
 * Chart.helpers. require_config.js maps "chart.js/helpers" to this module.
 */
define(['chartjs'], Chart => Chart.helpers);
