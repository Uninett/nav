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
  if ( $error != NULL ) {
    print $error->getHTML();
    $error = NULL;
  }

$dbhk = new DBHK($dbkcon);

$brukernavn = session_get('bruker'); $uid = session_get('uid');

if ( get_exist('fid') ) {
	session_set('match_fid', get_get('fid') );
}

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


  $l->addElement( array($match[$i][1],  // felt
			$type[$match[$i][2]], // type
			$match[$i][3], // verdi
			$valg ) 
		  );
}

print $l->getHTML();

print "<p>[ <a href=\"index.php\">oppdater <img src=\"icons/oppdater.gif\" alt=\"oppdater\" border=0> ]</a> ";
print "Antall filtermatcher: " . sizeof($match);


echo '<a name="nymatch"></a><p><h3>';
echo gettext("Legg til ny betingelse");
echo '</h3>';

/*
if (isset($matchfelt)) {
	$sa = "nymatch";
} else {
	$sa = "velgtype";
}
*/
print '<form name="form2" method="post" action="index.php?subaction=velgtype">';

?>
  <table width="100%" border="0" cellspacing="0" cellpadding="3">


    <tr>
    	<td width="30%"><p><?php echo gettext('Velg felt'); ?></p></td>
    	<td width="70%">
    	<select name="matchfelt" id="select" onChange="this.form.submit()">
<?php

// Viser oversikt over hvilke filtermatchfelter man kan velge...
$matchfields = $dbh->listMatchField(0);

foreach ($matchfields AS $matchfield) {
	$sel = "";
	if ($matchfield[0] == $matchfelt) { $sel = " selected"; }
	print '<option value="' . $matchfield[0] . '"' . $sel . '>' . $matchfield[1] . '</option>';
}

?>   	            
        </select>
        </td>
   	</tr>

    <tr>

<?php


// Valg av operator ----------------------------------------
if (post_exist('matchfelt') ) {
    print '</form>';
    print '<form name="form1" method="post" action="index.php?subaction=nymatch">';
}

echo '<td width="30%"><p>';
echo gettext("Velg betingelse");
echo '</p></td><td width="70%">';

if ( post_exist('matchfelt') ) {
/*
	$mf[0] = $data["name"];
	$mf[1] = $data["descr"];
	$mf[2] = $data["valuehelp"];
	$mf[3] = $data["valueid"];
	$mf[4] = $data["valuename"];
	$mf[5] = $data["valuecategory"];
	$mf[6] = $data["valuesort"];
	$mf[7] = $data["listlimit"];
	$mf[8] = $data["showlist"];
*/

    $matchfieldinfo = $dbh->matchFieldInfo(post_get('matchfelt'));

        print '<select name="matchtype" id="select">';
    
        if ( sizeof($matchfieldinfo[9]) > 0) {
            foreach ($matchfieldinfo[9] as $matchtype) {
                print '<option value="' . $matchtype . '">' . $type[$matchtype] . '</option>';
            }
        } else {
            print '<option value="0" selected>' . gettext("er lik") . '</option>';	
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



// Valg av verdi ----------------------------------------	
if ( post_exist('matchfelt') ) {


    
    $verdier = $dbhk->listVerdier(
        $matchfieldinfo[3],
        $matchfieldinfo[4],
        $matchfieldinfo[5],
        $matchfieldinfo[6]
    );
    /*
    echo "<pre>...\n";
    print_r($verdier);
    echo "</pre>";
    */
    
    if ($matchfieldinfo[8] == 't' ) {
      
        echo '<select name="verdi" id="select">';    
    
        // Traverser kategorier
        foreach ($verdier AS $cat => $catlist) {
            if ($cat != "") echo '<optgroup label="' . $cat . '">';
            foreach ($catlist AS $catelem) {
                echo ' <option value="' . $catelem[0] . '">' . $catelem[1] . '</option>' . "\n";
            }
            if ($cat != "") echo '</optgroup>';
        }
                    
        echo '</select>';
        
    } else {
        echo '<input name="verdi" size="40">';
    }    
    //echo '<input name="verdi" id="select" size="40">';

} else {
	print "<p>...";
}

?>

        </td></tr>

    <tr>
      <td>&nbsp;</td>
      
<?php

if ( post_exist('matchfelt') ) {
	$tekst = gettext("Legg til betingelse");
} else {
	$tekst = gettext("Velg matchefelt");
}

if (post_exist('matchfelt')) {
    echo '<input type="hidden" name="matchfelt" value="' . post_get('matchfelt') . '">';
}
print '<td align="right"><input type="submit" name="Submit" value="' . $tekst . '"></td>';


pg_close($dbkcon);

?>
    </tr>
  </table>

</form>


</td></tr>
</table>
