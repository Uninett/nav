<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p>Endre Passord</p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();
?>

<p>Her kan du endre passord for en bruker.

<?php

include("databaseHandler.php");
$dbh = new DBH($dbcon);

$brukernavn = session_get('bruker'); $uid = session_get('uid');

if (get_get('subaction') == 'endre') {

	if (post_exist('ebrukernavn') ) { 

		if (post_get('pass1') == post_get('pass2') ) {
			$dbh->endrePassord(post_get('ebrukernavn'), post_get('pass1'));

			print "<p><font size=\"+3\">OK</font>, passordet er endret for brukeren " . $ebrukernavn . ".";
			unset($ebrukernavn);			

		} else {
			print "<p><font size=\"+3\">Feil</font>, du skrev ikke to like passord, derfor vil det <b>ikke</b> bli endret.";
		}
		

	} else {
		print "<p><font size=\"+3\">Feil</font> oppstod, passord er <b>ikke</b> endret.";
	}

	// Viser feilmelding om det har oppstått en feil.
	if ( $error != NULL ) {
		print $error->getHTML();
		$error = NULL;
	}
  
}

print "<h3>Endre passord for en bruker</h3>";

?>

<form name="endrepassord" method="post" action="index.php?subaction=endre">

  <table width="100%" border="0" cellspacing="0" cellpadding="3">
    

    
    <tr>
    	<td width="30%"><p>Brukernavn</p></td>
    	<td width="70%"><input name="ebrukernavn" type="text" size="15" 
value="<?php echo $ebrukernavn; ?>"></select>
        </td>
   	</tr>

    <tr>
    	<td width="30%"><p>Passord</p></td>
    	<td width="70%"><input name="pass1" type="password" size="15" 
value=""></select>
        </td>
   	</tr>
   	
    <tr>
    	<td width="30%"><p>Passord igjen</p></td>
    	<td width="70%"><input name="pass2" type="password" size="15" 
value=""></select>
        </td>
   	</tr>   	
    <tr>
      <td>&nbsp;</td>
      <td align="right"><input type="submit" name="Submit" value="Endre Passord"></td>
    </tr>
  </table>

</form>


</td></tr>
</table>
