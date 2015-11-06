require(['libs/jquery'], function() {


    /**
     * Set even height on all report cards
     */
    function setMaxHeight($listElements) {
        console.log('Resizing');
        var maxHeight = 0;

        $listElements.height('auto');

        $listElements.each(function() {
            var height = $(this).height();
            if (height > maxHeight) {
                maxHeight = height;
            }
        });

        $listElements.height(maxHeight);

    }


    /**
     * Wait for page load
     */
    $(function() {

        var $listElements = $('#report-list li');
        if ($listElements.length > 1) {
            setMaxHeight($listElements);
            $(window).on('resize', function() {
                setMaxHeight($listElements);
            });
        }

    });

});
