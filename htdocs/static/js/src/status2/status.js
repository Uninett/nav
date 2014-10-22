require([
    'status/views',
    'libs/backbone',
], function (StatusView) {

    console.log('Initializing app');
    new StatusView();

    $('<span>&#178;</span>').hide().appendTo('.nav-header h2').fadeIn(3000);

});
