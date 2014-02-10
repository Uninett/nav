require(['libs/jquery', 'libs/jquery-ui-1.8.21.custom.min'], function () {

    var $container = $('#editimages');

    $(function () {
        var $cards = $container.find('.imagecard');

        $cards.each(addButtonListeners);

        if ($container.find('.imagecard').length >= 2) {
            addOrdering();
        }

        setTimeout(function () {
            $('.user-feedback .alert-box').each(function () {
                removeAlertBox($(this));
            });
        }, 3000);
    });

    function addButtonListeners(index, element) {
        var $element = $(element);
        addEditHandler($element);
        addDeleteHandler($element);
    }

    function addEditHandler($element) {
        $element.on('click', '.actions .edit', function () {
            var $titlecell = $element.find('.heading');
            if ($titlecell.find('input').length > 0) {
                return;
            }
            var titletext = $titlecell.html(),
                $input = $('<input type="text">').val(titletext);

            $input.keydown(function (event) {
                // Enter
                if (event.which === 13) {
                    saveTitle($(this));
                }
                // Escape
                if (event.which === 27) {
                    $titlecell.html(titletext);
                }
            });

            $titlecell.empty().append($input);
        });
    }

    function saveTitle($element) {
        var $card = $element.parents('.imagecard'),
            imageid = $card.attr('data-imageid'),
            $titlecell = $card.find('.heading'),
            title = $titlecell.find('input').val(),
            jqxhr = $.post('update_title', {'id': imageid, 'title': title});

        jqxhr.done(function () {
            $titlecell.html(title);
            createFeedback('Title updated', 'success');
        });

        jqxhr.fail(function () {
            createFeedback('Failed to update title', 'error');
        });

    }

    function addDeleteHandler($element) {
        $element.on('click', '.actions .delete', function (event) {
            if (confirm('Do you want to delete this image?')) {
                var $this = $(this),
                    $row = $this.parents('.imagecard'),
                    $imageid = $row.attr('data-imageid'),
                    jqxhr = $.post('delete_image', {'id': $imageid});

                jqxhr.done(function () {
                    location.reload();
                });

                jqxhr.fail(function () {
                    createFeedback('Failed to delete image', 'error');
                });
            }
        });
    }

    function addOrdering() {
        $container.sortable({
            items: '.imagecardcontainer',
            handle: '.drag',
            update: saveOrder,
            placeholder: "ui-state-highlight",
            forcePlaceholderSize: true
        });
        $container.find('.drag').disableSelection();
    }

    function saveOrder() {
        var jqxhr = $.post('update_priority', get_image_priorities());
        jqxhr.done(function () {
            createFeedback('Image order has been saved', 'success');
        });
        jqxhr.fail(function () {
            createFeedback('Could not save image order', 'error');
        });
    }

    function get_image_priorities() {
        var priorities = {};
        $container.find('.imagecard').each(function (index, element) {
            priorities[$(element).attr('data-imageid')] = index;
        });
        return priorities;
    }

    function createFeedback(message, type) {
        var $alertBox = $('<div>').addClass('alert-box').addClass(type).attr('data-alert', '').html(message),
            $close = $('<a href="#">').addClass('close').html('&times;').click(function () {
                removeAlertBox($alertBox);
        });

        $alertBox.append($close).appendTo('.user-feedback');
        setTimeout(function () {
            removeAlertBox($alertBox);
        }, 2000);
    }

    function removeAlertBox($alertBox) {
        $alertBox.fadeOut(function () {
            $(this.remove());
        });
    }

});
