<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p>Oppsett av filter</p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();
?>
<p>Her lager du et sett med betingelser som alle må være oppfylt for at en bestemt hendelse skal inkluderes av filteret. 
Hvis en eller flere av match'ene ikke slår til vil en hendelse altså ikke være med.
<p><a href="#nymatch">Legg til ny betingelse</A>

<?php

if (! $dbkcon = @pg_connect("user=manage dbname=manage password=eganam") ) {
  $error = new Error(2);
  $error->message = "Kunne ikke koble til database.";
}



include("databaseHandler.php");
$dbh = new DBH($dbcon);
$dbhk = new DBHK($dbkcon);

$brukernavn = session_get('bruker'); $uid = session_get('uid');

if ( get_exist('fid') ) {
	session_set('match_fid', get_get('fid') );
}


$felt[0] = 'Organisasjon';
$felt[1] = 'Sted (plass)';
$felt[2] = 'Sted (område)';
$felt[3] = 'Utstyrtype';
$felt[4] = 'Gruppe av utstyrstyper';
$felt[5] = 'Grad av viktighet';
$felt[6] = 'IP adresse';
$felt[7] = 'Utstyrsnavn';
$felt[8] = 'Portnummer';
$felt[9] = 'Tjeneste';
$felt[10] = 'Kilde';
$felt[11] = 'Alvorlighet';


$type[0] = 'er lik';
$type[1] = 'er større enn';
$type[2] = 'er større eller lik';
$type[3] = 'er mindre enn';
$type[4] = 'er mindre eller lik';
$type[5] = 'er ulik';
$type[6] = 'starter med';
$type[7] = 'slutter med';
$type[8] = 'inneholder';
$type[9] = 'regexp';
$type[10] = 'wildcard (? og *)';

$feltimpl = array(6,7,10,11); //Liste over felt som er implementert

$velgtype[0] = array();
$velgtype[1] = array();
$velgtype[2] = array();
$velgtype[3] = array();
$velgtype[4] = array();
$velgtype[5] = array(2, 4);
$velgtype[6] = array(0, 5);
$velgtype[7] = array(0, 5);
$velgtype[8] = array(0, 2, 4, 5);
$velgtype[9] = array();
$velgtype[10] = array(0, 5);
$velgtype[11] = array(0, 1, 2, 4, 5);

if ($subaction == 'slett') {

	if (session_get('match_fid') > 0) { 
	
		$dbh->slettFiltermatch(session_get('match_fid'), get_get('mid') );

		print "<p><font size=\"+3\">OK</font>, matchen er fjernet fra filteret.";

	} else {
		print "<p><font size=\"+3\">Feil</font>, matchen er <b>ikke</b> fjernet.";
	}

	// Viser feilmelding om det har oppstått en feil.
	if ( $error != NULL ) {
		print $error->getHTML();
		$error = NULL;
	}
  
}

if ($subaction == "nymatch") {
  print "<h3>Registrerer ny match...</h3>";
  
  $error = NULL;
  if ($navn == "") $navn = "Uten navn";
  if ($uid > 0) { 
    
    $matchid = $dbh->nyMatch(post_get('matchfelt'), post_get('matchtype'), 
    	post_get('verdi'), session_get('match_fid') );
    print "<p><font size=\"+3\">OK</font>, en ny betingelse (match) er lagt til for dette filteret.";
    
  } else {
    print "<p><font size=\"+3\">Feil</font>, ny match er <b>ikke</b> lagt til i databasen.";
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
		array('Felt', 'Betingelse', 'Verdi', 'Valg..'),
		array(40, 15, 25, 20),
		array('left', 'left', 'left', 'right'),
		array(true, true, true, false),
		0
);


print "<h3>Filtermatcher</h3>";

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

?>

<a name="nymatch"></a><p><h3>Legg til ny betingelse</h3>

<?php
if (isset($matchfelt)) {
	$sa = "nymatch";
} else {
	$sa = "velgtype";
}

print '<form name="form1" method="post" action="index.php?subaction=' . $sa . '">';


?>
  <table width="100%" border="0" cellspacing="0" cellpadding="3">

    <tr>
    	<td width="30%"><p>Velg felt</p></td>
    	<td width="70%">
    	<select name="matchfelt" id="select" onChange="this.form.submit()">
<?php
for ($t = 0; $t < sizeof($feltimpl); $t++) {
	if (isset($matchfelt) && ($matchfelt != $feltimpl[$t])) { continue; };
	$sel = "";
	if ($feltimpl[$t] == $matchfelt) { $sel = " selected"; }
	print '<option value="' . $feltimpl[$t] . '"' . $sel . '>' . $felt[$feltimpl[$t]] . '</option>';
}
?>   	            
        </select>
        </td>
   	</tr>


    <tr>
    	<td width="30%"><p>Velg betingelse</p></td>
    	<td width="70%">

    	
<?php

if ( isset($matchfelt) ) {

	print '<select name="matchtype" id="select">';

	if ( sizeof($velgtype[$matchfelt]) > 0) {
		foreach ($velgtype[$matchfelt] as $matchtype) {
			print '<option value="' . $matchtype . '">' . $type[$matchtype] . '</option>';
		}
	} else {
		print '<option value="0" selected>er lik</option>';
		print '<option value="5">er ulik</option>';		
	}
	print '</select>';
	
} else {
	print "<p>...";
}



?>    	
     
        
        </td>    	
   	</tr>
   	
    <tr>     
    	<td width="30%"><p>Sett verdi</p></td>
    	<td width="70%">
<?php    	
if ( isset($matchfelt) ) {



	switch ($matchfelt) {
		case 0: 
			print '<select name="verdi" id="select">';
			print '<option value="uninett">Uninett</option>';
			print '<option value="ntnu">NTNU</option>';			
			print '</select>';
			break;
		case 1: 
			$steder = $dbhk->listSted($sort);		
			print '<select name="verdi" id="select">';
			
			for ($i = 0; $i < sizeof($steder); $i++) {
				print '<option value="' . $steder[$i][0] . '">'. $steder[$i][1]. '</option>'. "\n";
			}
			print '</select>';
			break;
		case 2: 
			$steder = $dbhk->listOmraade($sort);	
			print '<select name="verdi" id="select">';

			for ($i = 0; $i < sizeof($steder); $i++) {
				print '<option value="' . $steder[$i][0] . '">'. $steder[$i][1]. '</option>' . "\n";
			}								
			print '</select>';
			break;
		case 3: 
			$typer = $dbhk->listType($sort);	
			print '<select name="verdi" id="select">';

			for ($i = 0; $i < sizeof($typer); $i++) {
				print '<option value="' . $typer[$i][0] . '">'. $typer[$i][1]. '</option>' . "\n";
			}	
			print '</select>';
			break;
		case 4: 
			$typer = $dbhk->listTypegruppe($sort);	
			print '<select name="verdi" id="select">';

			for ($i = 0; $i < sizeof($typer); $i++) {
				print '<option value="' . $typer[$i][0] . '">'. $typer[$i][1]. '</option>' . "\n";
			}	
			print '</select>';
			break;
			break;
		case 8: 
			print '<select name="verdi" id="select">';
			print '<option value="dns">DNS</option>';
			print '<option value="www">WWW</option>';
			print '<option value="dhcp">DHCP</option>';						
			print '</select>';
			break;
		case 10:
			print '<select name="verdi" id="select">';
			print '<option value="pping">pping</option>';
			print '<option value="serviceping">serviceping</option>';
			print '<option value="test">test</option>';
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
	$tekst = "Legg til betingelse";
} else {
	$tekst = "Velg matchefelt";
}

print '<td align="right"><input type="submit" name="Submit" value="' . $tekst . '"></td>';


pg_close($dbkcon);

?>
    </tr>
  </table>

</form>


</td></tr>
</table>
