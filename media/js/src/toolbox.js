require(['libs/jquery-ui-1.8.21.custom.min'], function () {
    $(function () {

        NAV.addGlobalAjaxHandlers();
        var selected_tools = $('#selected_tools');
        var deselected_tools = $('#deselected_tools');
        var layoutimage = $('.display-layout');
        var editbutton = $('.editbutton');
        var savebutton = $('.savebutton');
        var showonclick = $('.showonclick');

        editbutton.click(handleEditClick);
        savebutton.click(handleSaveClick);
        layoutimage.click(handleStyleClick);

        $('#deselected_tools, #selected_tools').sortable({
            connectWith: ".toollist",
            items: "li:not(.permanent)",
            disabled: true,
            placeholder: "ui-state-highlight",
            receive: checkIfEmpty
        }).disableSelection();


        function handleEditClick() {
            /* Toggle visibility state and enable sorting  */
            $(deselected_tools).show();
            $(editbutton).hide();
            $(showonclick).show();
            $('.toollist').sortable('enable');
            $('.toollist a').on('click', stopClick)
        }


        function handleSaveClick() {
            /* Toggle visibility states and send current state to server */
            $(deselected_tools).hide();
            $(editbutton).show();
            $(showonclick).hide();
            $.post('savetools', {'data': JSON.stringify(getTools())}, function () {
                $('.toollist').sortable('disable');
            });
            $('.toollist a').off('click', stopClick);
        }


        function stopClick() {
            return false;
        }


        function getTools() {
            /* Find all tools, their index and display setting */
            var tools = {};
            $('#selected_tools li a').each(function (index, tool) {
                var toolid = $(tool).attr('data-toolid');
                tools[toolid] = {"display": true, "index": index}
            });
            $('#deselected_tools li a').each(function (index, tool) {
                var toolid = $(tool).attr('data-toolid');
                tools[toolid] = {"display": false, "index": index}
            });
            return tools;
        }


        function checkIfEmpty(event, ui) {
            /* Check if 'selected tools' are empty, if so, cancel move
             * Alternative: Create droptarget when 'selected tools' is empty
             */
            if ($('li', selected_tools).length <= 0) {
                $(selected_tools).sortable("cancel");
            }
        }


        function handleStyleClick() {
            var layout = $(layoutimage).attr('data-value');
            $.post('changelayout', {'layout': layout}, function () {
                location.reload();
            });
        }

    });

});
