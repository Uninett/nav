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

        // Make sure all report links are of same height
        var $listElements = $('#report-list li');
        if ($listElements.length > 1) {
            setMaxHeight($listElements);
            $(window).on('resize', function() {
                setMaxHeight($listElements);
            });
        }


        // For availability reports, toggle incidents on click
        $('#record-table').on('click', function(event){
           var $target = $(event.target);
           if ($target.hasClass('toggle-incident')) {
               var $incident = $target.closest('.record-row').next();
               if ($incident.hasClass('hidden')) {
                   $incident.removeClass('hidden');
                   $target.text('Hide');
               } else {
                   $incident.addClass('hidden');
                   $target.text('Show');                   
               }
           }
       });
    });

});
