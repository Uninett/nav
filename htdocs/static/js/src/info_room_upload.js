require(['libs/jquery', 'libs/jquery-ui-1.8.21.custom.min'], function () {

    var $container = $('#editimages');

    $(function () {
        var $cards = $container.find('.imagecard');

        $cards.each(addButtonListeners);

        if ($container.find('.imagecard').length >= 2) {
            addOrdering();
        }
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
        });

        jqxhr.fail(function () {
            alert('Failed to update title');
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
                    alert('Failed to delete image');
                });
            }
        });
    }

    function addOrdering() {
        $container.sortable({
            items: '.imagecard',
            handle: '.drag',
            update: saveOrder
        });
        $container.find('.drag').disableSelection();
    }

    function saveOrder() {
        var jqxhr = $.post('update_priority', get_image_priorities());
        jqxhr.done(function () {});
        jqxhr.fail(function () {
            alert('Could not save image order');
        });
    }

    function get_image_priorities() {
        var priorities = {};
        $container.find('.imagecard').each(function (index, element) {
            priorities[$(element).attr('data-imageid')] = index;
        });
        return priorities;
    }

});
