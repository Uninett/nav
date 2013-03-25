require(['libs/jquery-ui-1.8.21.custom.min'], function () {
    $(function () {

        NAV.addGlobalAjaxHandlers();
        var $editbutton = $('.buttoncontainer .editbutton');
        var $savebutton = $('.buttoncontainer .savebutton');
        var $info = $('.buttoncontainer .info');
        var $tbody = $('#tool_list').find('tbody');
        var $switchcells = $tbody.find('.switch-cell');

        $editbutton.click(handleEditClick);
        $savebutton.click(handleSaveClick);

        /* Prepare sortable plugin - start disabled */
        $tbody.sortable({
            disabled: true
        }).disableSelection();


        function handleEditClick() {
            /* Toggle visibility state and enable sorting  */
            $editbutton.hide();

            $savebutton.show();
            $info.show();
            $switchcells.show();

            $tbody.sortable('enable');
        }


        function handleSaveClick() {
            /* Toggle visibility states and send current state to server */
            $editbutton.show();

            $savebutton.hide();
            $info.hide();
            $switchcells.hide();


            $.post('savetools', {'data': JSON.stringify(getTools())}, function () {
                $tbody.sortable('disable');
            });
        }


        function getTools() {
            /* Find all tools, their index and display setting */
            var tools = {};
            $('#tool_list').find('tbody tr').each(function (index, row) {
                var toolid = $(row).attr('data-toolid');

                tools[toolid] = {"display": getState(row), "index": index}
            });
            return tools;
        }

        function getState(row) {
            /* Get the selected input element from the switch */
            var textState = $(row).find("input:checked").attr('data-state');
            return textState === "on";
        }

    });

});
