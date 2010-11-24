$(document).ready(function(){
	add_change_listener_to_fields();
	position_saveall_buttons();
});

function add_change_listener_to_fields() {
	$(".ifalias, .vlanlist").change(function(){
		var row = $(this).parents("tr");
		$(row).addClass("changed");
		$(row).find("td").addClass("changed");
	});
}

function position_saveall_buttons() {
	/* 
	 * Wrap the buttons in a block-element with the width of 
	 * the table. Position them to the rigth in the block element.
	 */
	var width = $("table#portadmin-interfacecontainer").outerWidth();
	$("input.saveall_button").each(function(){
		var div = $("<div/>").width(width);
		$(this).wrap(div).addClass('right');
	});
}

function save_row(rowid) {
	/*
	 * This funcion does an ajax call to save the information given by the user
	 * when the save-button is clicked.
	 */
	
	// Fetch values from the fields
	var row = $("#" + rowid);
	var ifalias = $(row).find(".ifalias").val();
	var vlan = $(row).find(".vlanlist").val();
	
	// Post data and wait for json-formatted returndata. Display status information to user
	$.ajax({url: "save_interfaceinfo", 
			data: {'ifalias': ifalias, 'vlan': vlan, 'interfaceid': rowid}, 
			dataType: 'json',
			type: 'POST',
			success: function(data){
					display_callback_info(row, data);
					clear_changed_state(row)
				},
			error: function(request, errorMessage, errortype){
					var data = {}
					data.error = 1;
					data.message = errorMessage + " - Hm, perhaps try to log in again?"
					display_callback_info(row, data);
				}
	});
}

function bulk_save() {
	$("tr.changed").each(function(){
		save_row($(this).attr("id"));
	});
}

function clear_changed_state(row) {
	$(row).removeClass("changed");
	$(row).find("td").removeClass("changed");
}

function display_callback_info(row, data) {
	// Create new element
	var div = $("<div></div>").addClass("saveinfo");
	$("<p />").appendTo(div);
	$("body").append(div);

	// Add click-listener to remove element
	$(div).click(function(){
		$(this).remove();
	});
	
	// Calculate and set position
	var pos = $(row).find("td:last").offset(); // pos of last cell in row
	var left = pos.left + 30;
	var top = pos.top - 1;
	$(div).css({ "left": left + "px", "top": top + "px" });

	// Add correct layout
	if (data.error) {
		$(div).addClass("error");
	} else {
		$(div).addClass("success");
	}

	// Set message and show element
	$(div).find("p").html(data.message);
	$(div).show();

	// Automatically remove success messages
	if (!data.error) {
		$(div).fadeOut(6000, function(){
			$(this).remove();
		});
	}
}
