require(['libs/jquery-ui-1.8.21.custom.min'], function () {
    $(function () {

        var $editbutton = $('.buttoncontainer .editbutton');
        var $savebutton = $('.buttoncontainer .savebutton');
        var $info = $('.buttoncontainer .info');
        var $tbody = $('#tool_list').find('tbody');
        var $switchcells = $tbody.find('.switch-cell');

        $editbutton.click(handleEditClick);
        $savebutton.click(handleSaveClick);

        addSwitchChangeHandler();

        /* Prepare sortable plugin - start disabled */
        $tbody.sortable({
            disabled: true
        }).disableSelection();


        function addSwitchChangeHandler() {
            $tbody.on('change', '.switch-cell', function (event) {
                var $row = $(event.target).parents('tr');
                fadeToggle($row[0]);
            });
        }


        function fadeToggle(row) {
            /* Fade row based on state of switch */
            var $row = $(row);
            if (isOn(row)) {
                $row.fadeTo(1000, 1);
            } else {
                $row.fadeTo(1000, 0.5);
            }
        }


        function fadeAllIn() {
            $tbody.find('tr').each(function () {
                $(this).fadeTo(0, 1);
            })
        }


        function handleEditClick() {
            /* Toggle visibility state and enable sorting  */
            $editbutton.hide();

            $savebutton.show();
            $info.show();
            $switchcells.show();

            $tbody.find('tr').each(function () {
                fadeToggle(this);
            });

            $tbody.sortable('enable');
        }


        function handleSaveClick() {
            /* Toggle visibility states and send current state to server */
            var jqxhr = $.post('savetools',
                {'data': JSON.stringify(getTools())}
            );

            jqxhr.done(function () {
                $editbutton.show();

                $savebutton.hide();
                $info.hide();
                $switchcells.hide();

                fadeAllIn();

                $tbody.sortable('disable');

                alertUser(true);
            });

            jqxhr.fail(function () {
                alertUser(false);
            });
        }


        function getTools() {
            /* Find all tools, their index and display setting */
            var tools = {};
            $('#tool_list').find('tbody tr').each(function (index, row) {
                var toolid = $(row).attr('data-toolid');

                tools[toolid] = {"display": isOn(row), "index": index}
            });
            return tools;
        }

        function isOn(row) {
            /* Get the selected input element from the switch */
            var textState = $(row).find("input:checked").attr('data-state');
            return textState === "on";
        }

        function alertUser(success) {
            var $alertBox = $('<div/>').addClass('alert-box');

            if (success) {
                $alertBox.addClass('success');
                $alertBox.text('Changes saved');
            } else {
                $alertBox.addClass('alert');
                $alertBox.text('Failed to save changes');
            }

            $alertBox.on('click', function () {
                $(this).remove();
            });

            $('.buttoncontainer').before($alertBox);

        }

    });

});
