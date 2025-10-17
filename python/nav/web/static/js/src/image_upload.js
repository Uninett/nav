require(['jquery-ui'], function () {

    var $container = $('#editimages');

    $(function () {
        var $cards = $container.find('.imagecard');

        $cards.each(addButtonListeners);

        if ($container.find('.imagecard').length >= 2) {
            addOrdering();
        }

        setTimeout(function () {
            $('.user-feedback .alert-box.success').each(function () {
                removeAlertBox($(this));
            });
        }, 3000);

        /* Remove all feedback when clicked on */
        $('.user-feedback').click(function (event) {
            $(event.target).closest('.alert-box').remove();
        });
        var input = document.querySelector('.inputfile');
        var label = input.nextElementSibling,
            labelVal = label.innerHTML;

        input.addEventListener('change', function (e) {
            var fileName = '', title = '';
            if (this.files && this.files.length > 1) {
                console.log(this.files);
                fileName = ( this.getAttribute('data-multiple-caption') || '' ).replace('{count}', this.files.length);
                var names = [];
                for (var i = 0; i < this.files.length; i++) {
                    names.push(this.files[i].name);
                }
                title = names.join('\n');
            } else {
                fileName = e.target.value.split('\\').pop();
            }

            if (fileName) {
                label.querySelector('span').innerHTML = fileName;
            } else {
                label.innerHTML = labelVal;
            }
            label.setAttribute('title', title);

        });
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
            jqxhr = $.post(NAV.urls['image-update-title'], {'id': imageid, 'title': title});

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
                    jqxhr = $.post(NAV.urls['image-delete-image'], {'id': $imageid});

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
        var jqxhr = $.post(NAV.urls['image-update-priority'], get_image_priorities());
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
        const $alertBox = $('<div>').addClass('alert-box').addClass(type).attr('data-nav-alert', '').html(message),
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
