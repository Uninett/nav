<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext("Administrering av tilgjengelige match-felter"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();

echo "<p>" . gettext("Her kan du slette og opprette nye match-fetler med utgangspunkt i manage-databasen.");

echo '<p><a href="#nymatch">';
echo gettext("Legg til ny filtermatch") . "</a>";
echo "<p>";

$dbhk = $dbinit->get_dbhk();

/*
echo "dbhk:<pre>";
print_r($dbhk);
echo "</pre>";
*/

if (get_get('subaction') == "slett") {
	
    $dbh->slettMatchField(get_get('mfid') );
    print "<p><font size=\"+3\">" . gettext("OK</font>, match-feltet er slettet fra databasen.");

}

if (get_get('subaction') == "nymatch") {
  print "<h3>" . gettext("Registrerer ny filtermatch...") . "</h3>";
  
  $error = NULL;


  $fid = $dbh->nyttMatchFelt(
    post_get('name'), post_get('descr'), post_get('valuehelp'), post_get('valueid'),
    post_get('valuename'), post_get('valuecategory'), post_get('valuesort'), post_get('listlimit'),
    post_get('showlist'), post_get('datatype')
  );

    print "<p><font size=\"+3\">" . gettext("OK</font>, nytt match-felt er lagt inn i databasen og vil være tilgjengelig for bruk med engang. Felt-id-en er ") . $fid;



}

$l = new Lister( 301,
	array(gettext('id'), gettext('Navn'), gettext('Manage-referanse'), gettext('Valg...')),
	array(10, 30, 40, 20),
	array('left', 'left', 'left', 'right'),
	array(true, true, true, false),
	1
);


print "<h3>" . gettext("Tilgjengelige Match-felter") . "</h3>";


if ( get_exist('sortid') )
	$l->setSort(get_get('sort'), get_get('sortid') );


$fmlist = $dbh->listFilterMatchAdm($l->getSort() );

for ($i = 0; $i < sizeof($fmlist); $i++) {
  
  $valg = '<a href="index.php?subaction=slett&mfid=' . $fmlist[$i][0]. '">' .
    '<img alt="Delete" src="icons/delete.gif" border=0></a>';

  $l->addElement( array($fmlist[$i][0],  // id
			$fmlist[$i][1],  // navn
			$fmlist[$i][2], // referanse
			$valg
			) 
		  );
}

print $l->getHTML(1);

print "<p>[ <a href=\"index.php?action=" . $action. "\">" . gettext("oppdater") . " <img src=\"icons/refresh.gif\" alt=\"oppdater\" border=0> ]</a> ";
print gettext("Antall tilgjengelige match-felter: ") . sizeof($fmlist);
?>
<a name="nymatch"></a><p><h3>
<?php
echo gettext("Legg til nytt Match-felt"); 
?>
</h3>

<?php 

echo '<form name="nymatch" method="post" action="index.php?subaction=nymatch">';

echo '<table width="100%" border="0" cellspacing="0" cellpadding="3">';

echo '    <tr>';
echo '      <td width="30%">';
echo '<p>' . gettext("Navn") . '</p></td>';

echo '      <td width="70%">';
echo '<input name="name" type="text" size="40"></td>';

echo '    </tr>';


echo '    <tr>';
echo '      <td width="30%">' . gettext("Vis liste") . '</td>';

echo '      <td width="70%">';
echo '<input name="showlist" value="true" type="radio" checked> ' . gettext("Vis liste") . '<br>';
echo '<input name="showlist" value="false" type="radio"> ' . gettext("Vis input felt");
echo '      </td>';
echo '    </tr>';

echo '    <tr>';
echo '      <td width="30%">' . gettext("Maks listelengde") . '</td>';

echo '      <td width="70%">';
echo '<select name="listlimit">';
echo '<option value="100">100</option>';
echo '<option value="200">200</option>';
echo '<option value="300" selected>300</option>';
echo '<option value="500">500</option>';
echo '<option value="1000">1000</option>';
echo '<option value="10000">10000</option>';
echo '</select>';

echo '    </td></tr>';

echo '    <tr>';
echo '      <td width="30%">' . gettext("Datatype") . '</td>';

$dtype = array(
    0 => gettext("Streng"),
    1 => gettext("Tallverdi"),
    2 => gettext("IP-adresse")
);

echo '      <td width="70%">';
echo '<select name="datatype">';
foreach ($dtype AS $dval => $dt) {
    echo '<option value="' . $dval . '">' . $dt . '</option>' . "\n";
}
echo '</select>';

echo '    </td></tr>';





$f = $dbhk->listFelter();



echo '    <tr>';
echo '      <td width="30%">' . gettext("Manage (id)") . '</td>';

echo '      <td width="70%">';
echo '<select name="valueid" id="select">';
echo '<option value="." selected>' . gettext("Ingen referanse") . '</option>';   
// Traverser kategorier
foreach ($f AS $cat => $catlist) {
    if ($cat != "") echo '<optgroup label="' . $cat . '">';
    foreach ($catlist AS $catelem) {
        echo ' <option value="' . $cat . '.' . $catelem[0] . '">' . $catelem[0] . ' (' .$catelem[1]  . ') </option>' . "\n";
    }
    if ($cat != "") echo '</optgroup>';
}
echo '</select>';
echo '    </td></tr>';



echo '    <tr>';
echo '      <td width="30%">' . gettext("Manage (Navn)") . '</td>';

echo '      <td width="70%">';
echo '<select name="valuename" id="select">';   
echo '<option value="" selected>' . gettext("Ingen referanse") . '</option>';  
// Traverser kategorier
foreach ($f AS $cat => $catlist) {
    if ($cat != "") echo '<optgroup label="' . $cat . '">';
    foreach ($catlist AS $catelem) {
        echo ' <option value="' . $cat . '.' . $catelem[0] . '">' . $catelem[0] . ' (' .$catelem[1]  . ') </option>' . "\n";
    }
    if ($cat != "") echo '</optgroup>';
}
echo '</select>';
echo '    </td></tr>';




echo '    <tr>';
echo '      <td width="30%">' . gettext("Manage (Kategori)") . '</td>';

echo '      <td width="70%">';
echo '<select name="valuecategory" id="select">';   

echo '<option value="" selected>' . gettext("Ingen referanse") . '</option>';   
// Traverser kategorier
foreach ($f AS $cat => $catlist) {
    if ($cat != "") echo '<optgroup label="' . $cat . '">';
    foreach ($catlist AS $catelem) {
        echo ' <option value="' . $cat . '.' . $catelem[0] . '">' . $catelem[0] . ' (' .$catelem[1]  . ') </option>' . "\n";
    }
    if ($cat != "") echo '</optgroup>';
}
echo '</select>';
echo '    </td></tr>';




echo '    <tr>';
echo '      <td width="30%">' . gettext("Manage (Sorter)") . '</td>';

echo '      <td width="70%">';
echo '<select name="valuesort" id="select">';    
echo '<option value="" selected>' . gettext("Ingen referanse") . '</option>';
// Traverser kategorier
foreach ($f AS $cat => $catlist) {
    if ($cat != "") echo '<optgroup label="' . $cat . '">';
    foreach ($catlist AS $catelem) {
        echo ' <option value="' . $cat . '.' . $catelem[0] . '">' . $catelem[0] . ' (' .$catelem[1]  . ') </option>' . "\n";
    }
    if ($cat != "") echo '</optgroup>';
}
echo '</select>';
echo '    </td></tr>';





echo '    <tr>';
echo '      <td width="30%">';
echo '<p>' . gettext("Beskrivelse") . '</p></td>';

echo '      <td width="70%">';
echo '<textarea name="descr" cols="40" rows="6"></textarea></td>';

echo '    </tr>';

echo '    <tr>';
echo '      <td width="30%">';
echo '<p>' . gettext("Verdihjelp") . '</p></td>';

echo '      <td width="70%">';
echo '<textarea name="valuehelp" cols="40" rows="6"></textarea></td>';

echo '    </tr>';




echo '    <tr>';
echo '      <td colspan="2" align="right"><input type="submit" name="Submit" value="';
echo gettext('Legg til Match-felt') . '"></td>';
echo '    </tr>';


echo '</table></form>';
?>

</td></tr>
</table>
