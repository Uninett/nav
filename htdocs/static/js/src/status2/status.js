require([
    'status/views',
    'libs/backbone',
], function (StatusView) {

    console.log('Initializing app');
    new StatusView();

    $('<span>&#178;</span>').appendTo('.nav-header h2').css('display', 'inline').hide().fadeIn(3000);

});
