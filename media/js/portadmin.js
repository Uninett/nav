$(document).ready(function(){
	$(".ifalias, .vlanlist").change(function(){
		var row = $(this).parents("tr");
		$(row).addClass("changed");
		$(row).find("td").addClass("changed");
	});
	// place summary correctly
	position_summary();
});

function position_summary() {
	var pos = $("table#portadmin-interfacecontainer").offset();
	var width = $("table#portadmin-interfacecontainer").width();
	var left = pos.left + width + 5;
	var top = pos.top;
	$("div#summary").css({'left': left + 'px', 'top': top + 'px'});
}

function save_row(rowid, bulk) {
	/*
	 * This funcion does an ajax call to save the information given by the user
	 * when the save-button is clicked.
	 */
	
	// Fetch values from the fields
	var row = $("#" + rowid);
	var ifalias = $(row).find(".ifalias").val();
	var vlan = $(row).find(".vlanlist").val();
	
	// Post data and wait for json-formatted returndata. Display status information to user
	$.post("save_interfaceinfo", 
			{'ifalias': ifalias, 'vlan': vlan, 'interfaceid': rowid}, 
			function(data){
				if (bulk) {
					update_summary(row, data);
				} else {
					display_single_info(row, data);
				}
				clear_changed_state(row)
				
			}, 'json');
}

function bulk_save() {
	clean_summary();
	$("tr.changed").each(function(){
		save_row($(this).attr("id"), true);
	});
	display_summary();
}

function clear_changed_state(row) {
	$(row).removeClass("changed");
	$(row).find("td").removeClass("changed");
}

function clean_summary() {
	$("div#summary ul").empty();
	$("div#saveinfo").hide();
}

function update_summary(row, data) {
	var ifname = $(row).find("td:first-child").html();
	var listitem = $("<li />").append(ifname + ": " + data.message);
	if (data.error) {
		$(listitem).attr('class', 'error');
	} else {
		$(listitem).attr('class', 'success');
	}
	$("div#summary ul").append(listitem);
}

function display_summary() {
	$("div#summary").show();
}

function display_single_info(row, data) {
	var div = $("div#saveinfo");
	var pos = $(row).find("td:last").offset(); // pos of last cell in row
	var left = pos.left + 30;
	var top = pos.top - 7;
	
	if (data.error) {
		$(div).attr("class", "error");
	} else {
		$(div).attr("class", "success");
	}
	$(div).find("p").html(data.message);
	$(div).css({ "left": left + "px", "top": top + "px" });
	$(div).show();
}
