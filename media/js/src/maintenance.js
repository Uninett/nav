require.config({
    baseUrl: "/js/"
});
require(['src/plugins/quickselect', 'libs/jquery'], function (QuickSelect) {
    new QuickSelect('.quickselect');
});