require(['libs/jquery'], function () {

    $(function () {

        /* This jump function is used only for quicklink dropdowns */
        function jump(fe) {
            var opt_key = fe.selectedIndex;
            var uri_val = fe.options[opt_key].value;
            if (uri_val) {
                window.location = uri_val;
            }
            return false;
        }
        window.NAV = {'jump': jump};

        /* Add redirect to login if ajaxrequest on no session */
        $(document).ajaxError(function (event, request) {
            if (request.status === 401) {
                window.location = '/index/login/?origin=' + encodeURIComponent(window.location.href);
            }
        });

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
