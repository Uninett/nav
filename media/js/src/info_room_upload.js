require(['libs/jquery', 'libs/jquery-ui-1.8.21.custom.min'], function () {
    $(function () {
        var $table = $('#editimages'),
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
        $element.on('click', '.actions .edit', function (event) {
            var $this = $(this),
                $saveButton = $this.siblings('.save'),
                $titlecell = $this.parents('tr').find('.imagetitle'),
                titletext = $titlecell.html(),
                $input = $('<input type="text">').val(titletext);

            $this.hide();
            $saveButton.show();
            $titlecell.empty().append($input);
        });
    }

    function addSaveHandler($element) {
        $element.on('click', '.actions .save', function (event) {
            var $this = $(this),
                $editButton = $this.siblings('.edit'),
                $row = $this.parents('tr'),
                imageid = $row.attr('data-imageid'),
                $titlecell = $row.find('.imagetitle'),
                title = $titlecell.find('input').val(),
                jqxhr = $.post('update_title', {'id': imageid, 'title': title});

            jqxhr.done(function () {
                $this.hide();
                $editButton.show();
                $titlecell.html(title);
            });

            jqxhr.fail(function () {
                alert('Failed to update title');
            });
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
                    $row.remove();
                });

                jqxhr.fail(function () {
                    alert('Failed to delete image');
                });
            }
        });
    }

    function addOrdering($element, $sortable) {
        $element.on('click', '.activate', function () {
            $sortable.sortable('option', 'disabled', false);
        });
    }

});
