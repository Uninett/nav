<?php
/*
 * $Id$
 *
 * function for checking syntax on user input.
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

function check_syntax_address_sms(&$string) {
	// Removing non-relevant characters
	$string = preg_replace('/[^\+0-9]/', '', $string);
	
	// Removing trailing +47
	$string = preg_replace('/^(\+47)(.*?)$/', '$2', $string);
	
	// Check if the result contains 8 numbers...
	return preg_match('/^[0-9]{8}$/', $string);
}





?>