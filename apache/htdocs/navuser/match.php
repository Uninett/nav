<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext('Oppsett av filter'); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();

echo "<p>";
echo gettext("Her lager du et sett med betingelser som alle må være oppfylt for at en bestemt hendelse skal inkluderes av filteret. 
Hvis en eller flere av match'ene ikke slår til vil en hendelse altså ikke være med.");
echo '<p><a href="#nymatch">';
echo gettext("Legg til ny betingelse");
echo '</a>';


if (! $dbkcon = @pg_connect("user=manage dbname=manage password=eganam") ) {
  $error = new Error(2);
  $error->message = gettext("Kunne ikke koble til database.");
}

$dbhk = new DBHK($dbkcon);

$brukernavn = session_get('bruker'); $uid = session_get('uid');

if ( get_exist('fid') ) {
	session_set('match_fid', get_get('fid') );
}

define("ORG",0);
define("PLASS",1);
define("OMRADE",2);
define("UTSTYRSTYPE",3);
define("GRUPPE",4);
define("VIKTIG",5);
define("IP",6);
define("UTSTYRSNAVN",7);
define("PORTNUMMER",8);
define("TJENESTE",9);
define("KILDE",10);
define("HENDELSE",11);

//$felt[ORG] = gettext('Organisasjon');
//$felt[PLASS] = gettext('Sted (plass)');
//$felt[OMRADE] = gettext('Sted (område)');
$felt[UTSTYRSTYPE] = gettext('Utstyrtype');
//$felt[GRUPPE] = gettext('Gruppe av utstyrstyper');
$felt[VIKTIG] = gettext('Grad av viktighet');
$felt[IP] = gettext('IP adresse');
$felt[UTSTYRSNAVN] = gettext('Utstyrsnavn');
//$felt[PORTNUMMER] = gettext('Portnummer');
//$felt[TJENESTE] = gettext('Tjeneste');
$felt[KILDE] = gettext('Kilde');
$felt[HENDELSE] = gettext('Hendelse');

$type[0] = gettext('er lik');
$type[1] = gettext('er større enn');
$type[2] = gettext('er større eller lik');
$type[3] = gettext('er mindre enn');
$type[4] = gettext('er mindre eller lik');
$type[5] = gettext('er ulik');
$type[6] = gettext('starter med');
$type[7] = gettext('slutter med');
$type[8] = gettext('inneholder');
$type[9] = gettext('regexp');
$type[10] = gettext('wildcard (? og *)');

$velgtype[ORG] = array();
$velgtype[PLASS] = array();
$velgtype[OMRADE] = array();
$velgtype[UTSTYRSTYPE] = array(0,5);
$velgtype[GRUPPE] = array();
$velgtype[VIKTIG] = array(0,1,2, 4,5);
$velgtype[IP] = array(0, 5);
$velgtype[UTSTYRSNAVN] = array(0, 5);
$velgtype[PORTNUMMER] = array(0, 2, 4, 5);
$velgtype[TJENESTE] = array();
$velgtype[KILDE] = array(0, 5);
$velgtype[HENDELSE] = array(0, 5);

if ($subaction == 'slett') {

	if (session_get('match_fid') > 0) { 
	
		$dbh->slettFiltermatch(session_get('match_fid'), get_get('mid') );

		print "<p><font size=\"+3\">" . gettext("OK</font>, matchen er fjernet fra filteret.");

	} else {
		print "<p><font size=\"+3\">" . gettext("Feil</font>, matchen er <b>ikke</b> fjernet.");
	}

	// Viser feilmelding om det har oppstått en feil.
	if ( $error != NULL ) {
		print $error->getHTML();
		$error = NULL;
	}
  
}

if ($subaction == "nymatch") {
  print "<h3>" . gettext("Registrerer ny match...") . "</h3>";
  
  $error = NULL;
  if ($navn == "") $navn = gettext("Uten navn");
  if ($uid > 0) { 
    
    $matchid = $dbh->nyMatch(post_get('matchfelt'), post_get('matchtype'), 
    	post_get('verdi'), session_get('match_fid') );
    print "<p><font size=\"+3\">" . gettext("OK</font>, en ny betingelse (match) er lagt til for dette filteret.");
    
  } else {
    print "<p><font size=\"+3\">" . gettext("Feil</font>, ny match er <b>ikke</b> lagt til i databasen.");
  }

  // Viser feilmelding om det har oppstått en feil.
  if ( $error != NULL ) {
    print $error->getHTML();
    $error = NULL;
  }
  $subaction = "";
  unset($matchfelt);
  
}


$l = new Lister(111,
		array(gettext('Felt'), gettext('Betingelse'), gettext('Verdi'), gettext('Valg..') ),
		array(40, 15, 25, 20),
		array('left', 'left', 'left', 'right'),
		array(true, true, true, false),
		0
);


print "<h3>" . gettext("Filtermatcher") . "</h3>";

if ( get_exist('sortid') )
	$l->setSort(get_get('sort'), get_get('sortid') );
	
$match = $dbh->listMatch(session_get('match_fid'), $l->getSort() );

for ($i = 0; $i < sizeof($match); $i++) {

  $valg = '<a href="index.php?subaction=slett&mid=' . 
  	$match[$i][0] . '">' .
    '<img alt="Delete" src="icons/delete.gif" border=0>' .
    '</a>';


  $l->addElement( array($felt[$match[$i][1]],  // felt
			$type[$match[$i][2]], // type
			$match[$i][3], // verdi
			$valg ) 
		  );
}

print $l->getHTML();

print "<p>[ <a href=\"index.php\">Refresh <img src=\"icons/refresh.gif\" alt=\"Refresh\" border=0> ]</a> ";
print "Antall filtermatcher: " . sizeof($match);


echo '<a name="nymatch"></a><p><h3>';
echo gettext("Legg til ny betingelse");
echo '</h3>';

if (isset($matchfelt)) {
	$sa = "nymatch";
} else {
	$sa = "velgtype";
}

print '<form name="form1" method="post" action="index.php?subaction=' . $sa . '">';


?>
  <table width="100%" border="0" cellspacing="0" cellpadding="3">

    <tr>
    	<td width="30%"><p><?php echo gettext('Velg felt'); ?></p></td>
    	<td width="70%">
    	<select name="matchfelt" id="select" onChange="this.form.submit()">
<?php
foreach ($felt as $t => $value) {
	if (isset($matchfelt) && ($matchfelt != $t)) { continue; };
	$sel = "";
	if ($t == $matchfelt) { $sel = " selected"; }
	print '<option value="' . $t . '"' . $sel . '>' . $value . '</option>';
}
?>   	            
        </select>
        </td>
   	</tr>


    <tr>

<?php
echo '<td width="30%"><p>';
echo gettext("Velg betingelse");
echo '</p></td><td width="70%">';

if ( isset($matchfelt) ) {

	print '<select name="matchtype" id="select">';

	if ( sizeof($velgtype[$matchfelt]) > 0) {
		foreach ($velgtype[$matchfelt] as $matchtype) {
			print '<option value="' . $matchtype . '">' . $type[$matchtype] . '</option>';
		}
	} else {
		print '<option value="0" selected>' . gettext("er lik") . '</option>';
		print '<option value="5">' . gettext("er ulik") . '</option>';		
	}
	print '</select>';
	
} else {
	print "<p>...";
}



?>    	
     
        
        </td>    	
   	</tr>
   	
    <tr>     
    	<td width="30%"><p><?php echo gettext('Sett verdi'); ?></p></td>
    	<td width="70%">
<?php    	
if ( isset($matchfelt) ) {



	switch ($matchfelt) {
		case ORG: 
			print '<select name="verdi" id="select">';
			print '<option value="uninett">Uninett</option>';
			print '<option value="ntnu">NTNU</option>';			
			print '</select>';
			break;
		case PLASS: 
			$steder = $dbhk->listSted($sort);		
			print '<select name="verdi" id="select">';
			
			for ($i = 0; $i < sizeof($steder); $i++) {
				print '<option value="' . $steder[$i][0] . '">'. $steder[$i][1]. '</option>'. "\n";
			}
			print '</select>';
			break;
		case OMRADE: 
			$steder = $dbhk->listOmraade($sort);	
			print '<select name="verdi" id="select">';

			for ($i = 0; $i < sizeof($steder); $i++) {
				print '<option value="' . $steder[$i][0] . '">'. $steder[$i][1]. '</option>' . "\n";
			}								
			print '</select>';
			break;
		case UTSTYRSTYPE: 
			$typer = $dbhk->listType($sort);	
			print '<select name="verdi" id="select">';

			for ($i = 0; $i < sizeof($typer); $i++) {
				print '<option value="' . $typer[$i][0] . '">'. $typer[$i][1]. '</option>' . "\n";
			}	
			print '</select>';
			break;
		case GRUPPE: 
			$typer = $dbhk->listTypegruppe($sort);	
			print '<select name="verdi" id="select">';

			for ($i = 0; $i < sizeof($typer); $i++) {
				print '<option value="' . $typer[$i][0] . '">'. $typer[$i][1]. '</option>' . "\n";
			}	
			print '</select>';
			break;
			break;
		case PORTNUMMER: 
			print '<select name="verdi" id="select">';
			print '<option value="dns">DNS</option>';
			print '<option value="www">WWW</option>';
			print '<option value="dhcp">DHCP</option>';						
			print '</select>';
			break;

		case KILDE:
                       print '<select name="verdi" id="select">';
                       print '<option value="pping">pping</option>';
                       print '<option value="serviceping">serviceping</option>';
                       print '</select>';
                       break;
               case HENDELSE:
                         $typer = $dbhk->listEventtypes($sort);
                       print '<select name="verdi" id="select">';

                       for ($i = 0; $i < sizeof($typer); $i++) {
                               print '<option value="'. $typer[$i][0] . '">'. $typer[$i][0]. '</option>' . "\n";
                       }
                       print '</select>';
                       break;
						
		default:
			print '<input name="verdi" id="select" size="40">';
	}

} else {
	print "<p>...";
}
?>
<!--    	
    	
    	<select name="verdi" id="select">
          <option value="1">ITEA</option>
          <option value="2">Uninett AS</option>
          <option value="3">HiST</option>
          <option value="4">UiT</option>       
        </select>
   -->     
        
        </td>
   	</tr>

    <tr>
      <td>&nbsp;</td>
      
<?php

if ( isset($matchfelt) ) {
	$tekst = gettext("Legg til betingelse");
} else {
	$tekst = gettext("Velg matchefelt");
}

print '<td align="right"><input type="submit" name="Submit" value="' . $tekst . '"></td>';


pg_close($dbkcon);

?>
    </tr>
  </table>

</form>


</td></tr>
</table>
