<?php
/*
 * function for display of numbers.
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