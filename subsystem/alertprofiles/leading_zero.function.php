<?php
/*
 * $Id$
 * function for display of numbers.
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
 */


function leading_zeros( $aNumber, $intPart, $floatPart = NULL, $dec_point = NULL, $thousands_sep = NULL) {
}

function leading_zero( $aNumber, $intPart, $floatPart = NULL, $dec_point = NULL, $thousands_sep = NULL) {

	if ($aNumber == 0) return str_repeat("0", $intPart);

	$formattedNumber = $aNumber;
	if (! is_null($floatPart) ) {
		$formattedNumber = number_format($formattedNumber, $floatPart, $dec_point, $thousands_sep);
	}
	//if ($intPart > floor(log10($formattedNumber)))
	$formattedNumber = str_repeat("0", ($intPart + - 1 - floor(log10($formattedNumber)))) . $formattedNumber;

	return $formattedNumber;

}

?>