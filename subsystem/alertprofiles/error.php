<?php

/* 
 * Dette er en generell feilmeldingsklasse. 
 */
class Error {
	var $type;
	var $message;
	var $type_name;
	var $sev; 

	function Error ($errtype, $sev = 0) {
		$this->type_name = array(
				gettext('Uknown error'),
				gettext('Log in error'), 
				gettext('Database error'),
				gettext('Security error'),
				gettext('IO error'),
				gettext('AlertProfiles PHP Errorhandler')
				);
		$this->type = $errtype;
		$this->sev = $sev;
	}

	function getHeader () {
		return $this->type_name[$this->type];
	}

	function setMessage ($msg) {
		$this->message = $msg;
	}

	function isSevere() {
		return ($this->sev == 1);
	}

	function getHTML () {
		$html =  "<table width=\"100%\" class=\"feilWindow\"><tr><td class=\"mainWindowHead\"><h2>";
		$html .= $this->GetHeader();
		$html .= "</h2></td></tr>";
		$html .= "<tr><td><p>" . $this->message . "</td></tr></table>";
		return $html;
	}

}

global $error;

// set the error reporting level for this script
//error_reporting(E_ALL);


// error handler function
function myErrorHandler($errno, $errstr, $errfile, $errline) 
{
	global $error;
	switch ($errno) {
		case E_ERROR:
			if (AP_DEBUG_LEVEL > 0) {
				echo "AlertProfiles error-handler:<b>FATAL</b> [$errno] <h3>$errstr</h3><p>\n";
				echo "  Fatal error in line $errline of file $errfile";
				echo ", PHP " . PHP_VERSION . " (" . PHP_OS . ")<br />
					$errfile [$errline]\n";
				echo "Aborting...<br />\n";
			}
			exit(1);
			break;
		case E_ERROR:
			$ne = new Error(5, 1);
			$ne->message = gettext("<b>ERROR</b> [$errno] <h3>$errstr</h3><p>
					$errfile<br>on line [$errline]");
			$error[] = $ne;
			break;
		case E_NOTICE:
			$ne = new Error(5);
			$ne->message = gettext("AlertProfiles error-handler:<b>WARNING</b> [$errno] <h3>$errstr</h3><p>
					$errfile<br>on line [$errline]\n");
			$error[] = $ne;
			break;
		default:
			$ne = new Error(5, 1);
			$ne->message = gettext("AlertProfiles error-handler:Unkown error type: [$errno] <h3>$errstr</h3><p>
					$errfile<br>on line [$errline]\n");
			$error[] = $ne;
			break;
	}
}

function flusherrors() {
	global $error;
	/* 	print "<pre>ERRORS:"; */
	/* 	print_r($error); */
	/* 	print "</pre>"; */

	while (is_array($error) && $err = array_pop($error)) {

		$errorlvl = isset($_GET['debug']) ? $_GET['debug'] : AP_DEBUG_LEVEL;

		if ( ($err->isSevere()  and $errorlvl > 0 ) or 
				($errorlvl > 1) ) {
			if (AP_DEBUG_TYPE == AP_DEBUG_INLINE) {
				print '<table width="100%" class="feilWindow">
					<tr><td class="mainWindowHead" colspan="2">
					<h2>';
				print $err->GetHeader();
				print "</h2></td></tr>";

				print '<tr><td><img alt="error" src="images/warning.png"></td>
					<td><p>';
				print $err->message . "</td></tr></table>";
			} elseif (AP_DEBUG_TYPE == AP_DEBUG_FILE)  {
				print "<table width=\"100%\" class=\"feilWindow\"><tr><td class=\"mainWindowHead\"><h2>";
				print "FILE";
				print "</h2></td></tr>";
				print "<tr><td><p>" . $err->message . "</td></tr></table>";
			}
		}

	}
}

?>
