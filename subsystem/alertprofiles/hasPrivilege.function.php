<?php
/*
 * $Id$
 *
 * function wrapper for hasPrivilege.
 * PATH_BIN contains the path to the hasPrivilege.py script.
 *
 * Copyright 2002-2004 UNINETT AS
 * 
 * This file is part of Network Administration Visualized (NAV)
 *
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 *
 * Authors: Andreas Aakre Solberg <andreas.solberg@uninett.no>
 *
 */


function access_address_type($username, $addresstype) {
	$atypes = array(
		1 => 'e-mail',
		2 => 'sms',
	);
	$returncode = 'NA';
	$interpreter = $_ENV['PYTHONHOME'] ? $_ENV['PYTHONHOME'] . '/bin/python' : "";
	
	$cmd = $interpreter . ' ' . PATH_BIN . '/hasPrivilege.py ' . escapeshellcmd($username) . ' alert_by ' . $atypes[$addresstype];
	system($cmd, $returncode);
	return ($returncode === 0);
}
function access_sms($username) {
	return access_address_type($username, 2);
}

?>