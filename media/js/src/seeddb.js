require.config({baseUrl: "/js/"});

require(['src/plugins/checkbox_selector', 'src/plugins/quickselect', 'libs/jquery'], function(CheckboxSelector, QuickSelect){
    $(function() {
        new CheckboxSelector('#select', '.selector').add();
        new QuickSelect('.quickselect');
    });
});
