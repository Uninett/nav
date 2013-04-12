require(['libs/jquery', 'libs/jquery-ui-1.8.21.custom.min'], function () {

    var tableSelector = '#editimages';

    $(function () {
        var $table = $(tableSelector),
            $orderButtons = $('#orderbuttons')

        addButtonListeners($table);

        if ($orderButtons) {
            var $tbody = $table.find('tbody');

            var $sortable = $tbody.sortable({
                items: '.imagerow',
                disabled: true
            });
            $tbody.disableSelection();
            addOrdering($orderButtons, $sortable);
        }
    });

    function addButtonListeners($element) {
        addEditHandler($element);
        addSaveHandler($element);
        addDeleteHandler($element);
    }

    function addEditHandler($element) {
        $element.on('click', '.actions .edit', function () {
            var $this = $(this),
                $saveButton = $this.siblings('.save'),
                $titlecell = $this.parents('tr').find('.imagetitle'),
                titletext = $titlecell.html(),
                $input = $('<input type="text">').val(titletext);

            $input.keypress(function (event) {
                if (event.which == 13) {
                    saveTitle($(this));
                }
            });

            $this.hide();
            $saveButton.show();
            $titlecell.empty().append($input);
        });
    }

    function addSaveHandler($element) {
        $element.on('click', '.actions .save', function () {
            saveTitle($(this));
        });
    }

    function saveTitle($element) {
        var $row = $element.parents('tr'),
            imageid = $row.attr('data-imageid'),
            $titlecell = $row.find('.imagetitle'),
            $saveButton = $row.find('.save'),
            $editButton = $row.find('.edit'),
            title = $titlecell.find('input').val(),
            jqxhr = $.post('update_title', {'id': imageid, 'title': title});

        jqxhr.done(function () {
            $saveButton.hide();
            $editButton.show();
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
                    $row = $this.parents('tr'),
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

    function addOrdering($element, $sortable) {
        $element.on('click', '.activate', function () {
            var $this = $(this);
            $this.hide();
            $this.siblings('.save').show();
            $sortable.sortable('option', 'disabled', false);
        });

        $element.on('click', '.save', function () {
            var $this = $(this),
                jqxhr = $.post('update_priority', get_image_priorities());

            jqxhr.done(function () {
                $this.hide();
                $this.siblings('.activate').show();
                $sortable.sortable('option', 'disabled', true);
            });

            jqxhr.fail(function () {
                alert('Could not save image order');
            });
        });
    }

    function get_image_priorities() {
        var priorities = {};
        $(tableSelector).find('.imagerow').each(function (index, element) {
            priorities[$(element).attr('data-imageid')] = index;
        });
        return priorities;
    }

});
