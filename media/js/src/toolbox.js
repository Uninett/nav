require(['libs/jquery-ui-1.8.21.custom.min'], function () {
    $(function () {

        NAV.addGlobalAjaxHandlers();
        var $editbutton = $('.buttoncontainer .editbutton');
        var $savebutton = $('.buttoncontainer .savebutton');
        var $info = $('.buttoncontainer .info');
        var $tbody = $('#tool_list').find('tbody');

        $editbutton.click(handleEditClick);
        $savebutton.click(handleSaveClick);

        $tbody.sortable({
            disabled: true
        }).disableSelection();


        function handleEditClick() {
            /* Toggle visibility state and enable sorting  */
            $editbutton.hide();
            $savebutton.show();
            $info.show();
            $tbody.sortable('enable');
        }


        function handleSaveClick() {
            /* Toggle visibility states and send current state to server */
            $editbutton.show();
            $savebutton.hide();
            $info.hide();
            $.post('savetools', {'data': JSON.stringify(getTools())}, function () {
                $('.toollist').sortable('disable');
            });
        }


        function getTools() {
            /* Find all tools, their index and display setting */
            var tools = {};
            $('#tool_list').find('tbody tr').each(function (index, tool) {
                var toolid = $(tool).attr('data-toolid');
                tools[toolid] = {"display": true, "index": index}
            });
            return tools;
        }

    });

});
