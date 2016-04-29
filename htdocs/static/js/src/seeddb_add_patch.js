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
        var $modal = $('#add-patch-modal');
        var $interfaceNameElement = $modal.find('.interfacename');
        var $interfaceIdElement = $modal.find('#interface-id');
        var $cableIdElement = $modal.find('#cable-search');
        var $form = $('#add-patch-form');
        var $feedback = $modal.find('.alert-box');


        /* Open modal and provide user with interface for creating patches */
        $('#interface-table').on('click', '.add-patch', function(event){
            $feedback.hide();
            var $button = $(event.target);
            var $row = $button.closest('tr');
            var $cells = $row.find('td');
            var interfacename = $cells.get(0).innerHTML;
            var interfacealias = $cells.get(1).innerHTML;
            var interfaceid = $row.data('interfaceid');
            $interfaceNameElement.text(interfacename + ' - ' + interfacealias);
            $interfaceIdElement.val(interfaceid);
            $modal.foundation('reveal', 'open');
        });


        /* When user clicks the save-patch button, create a patch and give feedback */
        $('#save-patch-button').on('click', function(event){
            event.preventDefault();
            if ($cableIdElement.val() > 0) {
                var request = $.post(NAV.urls.seeddb_patch_save, $form.serialize());
                request.done(function(){
                    reloadCableCell($interfaceIdElement.val());
                    $cableIdElement.select2('val','');
                    $modal.foundation('reveal', 'close');
                });
                request.fail(function(response){
                    $feedback.show().html('Error saving patch - ' + response.responseText);
                });
            } else {
                $feedback.show().html('Please choose a cable');
            }
        });


        /* Update the cell with cable info */
        function reloadCableCell(interfaceid) {
            var request = $.get(NAV.urls.seeddb_patch_load_cell,
                                { interfaceid: interfaceid });
            request.done(function(data){
                var $row = $('tr[data-interfaceid=' + interfaceid + ']');
                $row.find('.patch-cell').html(data);
                $row.find('.patch-button-cell').empty();
            });
        }

    });

});
