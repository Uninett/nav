<?php
/*
 * Constant and variables global for NAV Alert Profiles
 *
 */

// PATHS

define("PATH_DB", "/usr/local/nav/local/etc/conf/");
define("PATH_BIN", "/usr/local/nav/navme/bin/");

/*
 * Matchfield operators
 *
 */
global $type;
$type = array (
	0 => gettext('equals'),
	1 => gettext('is greater'),
	2 => gettext('is greater or equal'),
	3 => gettext('is less'),
	4 => gettext('is less or equal'),
	5 => gettext('not equals'),
	6 => gettext('starts with'),
	7 => gettext('ends with'),
	8 => gettext('contains'),
	9 => gettext('regexp'),
	10=> gettext('wildcard (? og *)')
);



?>