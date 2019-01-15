require(['libs/select2.min'], function(){
    $(function(){
        /* Enable search for cables in the modal */
        $('#cable-search').select2({
            ajax: {
                url: '/api/1/cabling/',
                dataType: 'json',
                data: function(term) {
                    return {
                        search: term,
                        room: NAV.seeddb_add_patch.room,
                        available: 1
                    };
                },
                results: function(data) {
                    return {
                        results: data.results.map(function(obj){
                            return {
                                id: obj.id,
                                text: 'Jack ' + obj.jack + ' - ' +
                                    [obj.building, obj.target_room, obj.description].filter(function(x){
                                        return Boolean(x);
                                }).join(', ')
                            };
                        })
                    };
                }
            },
            minimumInputLength: 2
        });

        /* Global variables */
        var $addModal = $('#add-patch-modal');
        var $removeModal = $('#remove-patch-modal');
        var $cableIdElement = $addModal.find('#cable-search');
        var $addForm = $addModal.find('form');
        var $removeForm = $removeModal.find('form');

        /* Open modal and provide user with interface for creating patches */
        $('#interface-table').on('click', '.patch-button-cell button', function(event){
            var $button = $(event.target);
            var $row = $button.closest('tr');
            var $cells = $row.find('td');
            var interfacename = $cells.get(0).innerHTML;
            var interfacealias = $cells.get(1).innerHTML;
            var interfaceid = $row.data('interfaceid');

            var $modal = $button.hasClass('add-patch') ? $addModal : $removeModal;
            $modal.find('.interfacename').text(interfacename + ' - ' + interfacealias);
            $modal.find('.interfaceid').val(interfaceid);
            $modal.find('.alert-box').hide();
            $modal.foundation('reveal', 'open');
        });


        /* When user clicks the save-patch button, create a patch and give feedback */
        $('#save-patch-button').on('click', function(event){
            event.preventDefault();
            var $interfaceIdElement = $addModal.find('.interfaceid'),
                $feedback = $addModal.find('.alert-box');
            if ($cableIdElement.val() > 0) {
                var request = $.post(NAV.urls.seeddb_patch_save, $addForm.serialize());
                request.done(function(){
                    reloadCableCell($interfaceIdElement.val(), 'add');
                    $cableIdElement.select2('val','');
                    $addModal.foundation('reveal', 'close');
                });
                request.fail(function(response){
                    $feedback.show().html('Error saving patch - ' + response.responseText);
                });
            } else {
                $feedback.show().html('Please choose a cable');
            }
        });


        /* When user clicks the remove-patch button, delete the patch */
        $('#remove-patch-button').on('click', function(event){
            event.preventDefault();
            var $interfaceIdElement = $removeModal.find('.interfaceid'),
                $feedback = $removeModal.find('.alert-box');

            var request = $.post(NAV.urls.seeddb_patch_remove, $removeForm.serialize());
            request.done(function(){
                reloadCableCell($interfaceIdElement.val(), 'remove');
                $removeModal.foundation('reveal', 'close');
            });
            request.fail(function(response){
                $feedback.show().html('Error removing patch - ' + response.responseText);
            });
        });


        /* User cancels remove of patch */
        $('#cancel-remove-patch-button').on('click', function(event){
            $removeModal.foundation('reveal', 'close');
        });


        /* Update the cell with cable info and add appropriate button */
        function reloadCableCell(interfaceid, action) {
            var request = $.get(NAV.urls.seeddb_patch_load_cell,
                                { interfaceid: interfaceid });
            request.done(function(data){
                var $row = $('tr[data-interfaceid=' + interfaceid + ']');
                $row.find('.patch-cell').html(data);
                var $buttonCell = $row.find('.patch-button-cell');
                if (action === 'add') {
                    $buttonCell.html('<button class="table-button remove-patch secondary">Remove patch</button>');
                } else {
                    $buttonCell.html('<button class="table-button add-patch">Add patch</button>');
                }
            });
        }

    });

});
