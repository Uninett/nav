require(['plugins/checkbox_selector', 'plugins/quickselect', 'libs/jquery'], function(CheckboxSelector, QuickSelect){
    $(function() {
        new CheckboxSelector('#select', '.selector').add();
        new QuickSelect('.quickselect');
    });
});
