require(['libs/jquery'], function () {
    $(function () {
        // Find all divs with medium-2 class inside navbarlink form
        // Slice so we get the last two empty elements
        // Clear the content so the checkboxes are removed
        var length = $('.link-delete').length;
        $('.link-delete').slice(length-2,length).empty()      
    });
});
