require([], function () {
    $(function () {
        // Find all delete buttons in the link form
        // Slice so we get the last two empty elements
        // Clear the content so the checkboxes are removed
        var length = $('.link-delete').length;
        $('.link-delete').slice(length-2,length).empty()      
    });
});
