require(['plugins/accordion_maker', 'default', 'libs/foundation.min'], function (accordionMaker) {
    NAV.addGlobalAjaxHandlers();
    $(document).foundation();
    accordionMaker($('.tabs'));

});
