require(['jquery'], function() {

    var subscriptionReloadEvent = "nav.events.reload-subscription-list";
    var storageKey = 'nav-business-deleted-subscription';
    var $undoContainer = $("#undounsubscribe");

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


        addSubscriptionListener();
        addRefreshSubscriptionListListener();
        addRemoveSubscriptionListener();
        addUndoUnsubscribeListener();
    });

    /**
     * Listen to form submits for adding subscriptions. Submit form by ajax and
     * reload subscription list
     */
    function addSubscriptionListener() {
        $('#subscription-form').on('submit', function(event) {
            event.preventDefault();
            var $form = $(this);
            $.post($form.attr("action"), $form.serialize())
             .then(function() {
                 if (_.has($form.get(0).elements, 'new_address')) {
                     window.location.reload();
                 } else {
                     $('body').trigger(subscriptionReloadEvent);
                 }
             });
        })
    }

    /** Reload subscription list when subscription reload events are triggered */
    function addRefreshSubscriptionListListener() {
        var $subscriptionList = $('#subscription-list');
        $('body').on(subscriptionReloadEvent, function() {
            $.get(NAV.urls.render_report_subscriptions, function(html) {
                $subscriptionList.html(html);
            })
        })
    }

    /** Remove subscription when unsubscribe button is clicked, then reload subscription list */
    function addRemoveSubscriptionListener() {
        var $subscriptionList = $('#subscription-list');
        $subscriptionList.on('click', 'button', function(event) {
            var serializedSubscription = $(this).data('subscriptionObject');
            $.post(NAV.urls.remove_report_subscription, {
                subscriptionId: $(this).data('subscriptionId')
            }).then(function() {
                localStorage.setItem(storageKey, JSON.stringify(serializedSubscription));
                $('body').trigger(subscriptionReloadEvent);
                $undoContainer.css('display', 'flex');
            })
        })
    }

    function addUndoUnsubscribeListener() {
        $undoContainer.on('click', 'button', function() {
            var data = JSON.parse(localStorage.getItem(storageKey));
            $.post(NAV.urls.save_report_subscription, data)
             .then(function() {
                 $('body').trigger(subscriptionReloadEvent);
                 $undoContainer.hide();
             })
        })
    }

});
