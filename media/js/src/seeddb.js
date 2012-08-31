require.config({baseUrl: "/js/"});

require(['src/plugins/checkbox_selector', 'src/plugins/quickselect', 'libs/jquery'], function(CheckboxSelector){
    $(function() {
        new CheckboxSelector('#select', '.selector').add();
    });
});
