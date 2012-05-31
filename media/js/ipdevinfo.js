var ipdevinfo = {}

ipdevinfo.add_ds_toggler = function() {
    var clicknode = $('.datasources .toggle-datasources');
    if (clicknode) {
	var rows = $('.datasources tr.hidden');
	var textnode = $('span.infotext', clicknode);
	var hellip = $('span.hellip', clicknode);
	var nodetext = '';
	$(clicknode).toggle(
	    function() {
		$(rows).show();
		$(hellip).hide();
		nodetext = $(textnode).text();
		$(textnode).text('Show less');
	    },
	    function() {
		$(rows).hide();
		$(hellip).show();
		$(textnode).text(nodetext);
	    }
	);
    }
}

$(document).ready(function() {
    ipdevinfo.add_ds_toggler();
});
