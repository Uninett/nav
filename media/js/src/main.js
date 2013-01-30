require(['libs/jquery'], function () {

    $(function () {
        /* Add toggler for navbar visibility */
        var navbarExpandButton = $('#navbartoggler').find('.expand'),
            navbarCollapseButton = $('#navbartoggler').find('.collapse');

        navbarExpandButton.click(function () {
            $('#navpath, #navbarlogininfo, #navbarquicklinks, #navbarlinks').show();
            navbarExpandButton.hide();
            navbarCollapseButton.show();
        });

        navbarCollapseButton.click(function () {
            $('#navpath, #navbarlogininfo, #navbarquicklinks, #navbarlinks').hide();
            navbarExpandButton.show();
            navbarCollapseButton.hide();
        });

    });
});
