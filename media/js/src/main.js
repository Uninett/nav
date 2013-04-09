require(['plugins/accordion_maker', 'libs/foundation.min'], function (accordionMaker) {
    $(document).foundation();

    accordionMaker($('.tabs'));

});
