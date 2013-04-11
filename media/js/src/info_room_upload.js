require(['libs/jquery'], function () {
    $(function () {
        if ($('#editimages').length) {
            addButtonListeners($('#editimages'));
        }
    });

    function addButtonListeners($element) {
        $element.on('click', '.actions .edit', function (event) {
            var $this = $(this),
                $saveButton = $this.siblings('.save'),
                $titlecell = $this.parents('tr').find('.imagetitle'),
                $titletext = $titlecell.html(),
                $input = $('<input type="text">').val($titletext);

            $this.hide();
            $saveButton.show();
            $titlecell.empty().append($input);
        });

        $element.on('click', '.actions .save', function (event) {
            var $this = $(this),
                $editButton = $this.siblings('.edit'),
                $row = $this.parents('tr'),
                $imageid = $row.attr('data-imageid'),
                $titlecell = $row.find('.imagetitle'),
                $title = $titlecell.find('input').val(),
                jqxhr = $.post('update_title', {'id': $imageid, 'title': $title});

            jqxhr.done(function () {
                $this.hide();
                $editButton.show();
                $titlecell.html($title);
            });

            jqxhr.fail(function () {
                alert('Failed to update title');
            });
        });

        $element.on('click', '.actions .delete', function (event) {
            var ok = confirm('Do you want to delete this image?');

            if (ok) {
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
});
