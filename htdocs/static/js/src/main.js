require([
    'plugins/accordion_maker',
    'default',
    'libs/foundation.min',
    'libs/select2.min',
    'plugins/megadrop'
], function (accordionMaker) {
    $(function () {
        $(document).foundation();   // Apply foundation javascript on load
        accordionMaker($('.tabs')); // Apply accordionmaker for tabs
        $('select.select2').select2();
    });
});


