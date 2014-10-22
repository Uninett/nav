require([
    'status/views',
    'libs/backbone',
], function (StatusView) {

    console.log('Initializing app');
    new StatusView();

    $('.nav-header h2').append('&#178;');

});
