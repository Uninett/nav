<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<?php
echo '<p>Filter setup</p>';
if ( get_exist('fid') ) {
	session_set('match_fid', get_get('fid') );
}
$utstginfo = $dbh->utstyrfilterInfo( session_get('match_fid') );
echo '<div class="subheader">' . $utstginfo[0] . 
'<p style="font-size: x-small; font-weight: normal; margin: 2px; text-align: left"><img src="icons/person100.gif"> This is a public filter, owned by the administrators. You are free to use this filter to set up your own filter groups, but you cannot change the filter composition.</div>';

?>

</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();

echo "<p>";
echo gettext("Here is a read only overview of the requested filter. The composition of the filter with the list of conditions for an alert to match this filter, is shown below:");



$dbhk = $dbinit->get_dbhk();
$brukernavn = session_get('bruker'); $uid = session_get('uid');



$l = new Lister(111,
    array(gettext('Field'), gettext('Condition'), gettext('Value') ),
    array(40, 15, 25, 20),
    array('left', 'left', 'left'),
    array(true, true, true),
    0
);


print "<p>";

if ( get_exist('sortid') )
	$l->setSort(get_get('sort'), get_get('sortid') );
	
$match = $dbh->listMatch(session_get('match_fid'), $l->getSort() );

for ($i = 0; $i < sizeof($match); $i++) {
	
	$l->addElement( array(
		$match[$i][1],  // felt
		$type[$match[$i][2]], // type
		$match[$i][3]
		) 
	);
}

print $l->getHTML();

print "<p>[ <a href=\"index.php?action=equipment-filter-view\">" . gettext("update") . " <img src=\"icons/refresh.gif\" class=\"refresh\" alt=\"oppdater\" border=0> ]</a> ";
print "Number of conditions: " . sizeof($match);

?>

</td></tr>
</table>
