require(["libs/jquery.tablesorter.min"], function (tablesorter) {
        $(document).ready(function () {
            
            // Data parameters for tablesorter
            headerData= {};
            textExtractionData = {}
            // Get all the th elements in the table
            headings = $('#tracker-table').children('thead').children('tr').children('th');

            // We don't sort the icon cell and sort IP as text from the span
            $.each(headings, function(index, cell) {
                if(cell.innerHTML == "") 
                    headerData[index] = {sorter : false};

                if(cell.innerHTML == "IP") {
                    textExtractionData[index] = function(node, table, cellIndex){
                            return $(node).find('span').text()
                        ;}
                    headerData[index] = {sorter : 'text', string: 'min'};
                }
            });
            
            // Enable tablesorter
            $('#tracker-table').tablesorter({
                headers: headerData,
                textExtraction: textExtractionData,
                widgets: ['zebra']});
            });
            
            // If the form is reloaded, display correct data
            if($('#id_days').val() == "-1") {
                $('#id_hide').attr('checked', 'true');
                $('#id_days').attr('disabled', 'disabled');
                $('#id_days').val("7");
            }
        });
