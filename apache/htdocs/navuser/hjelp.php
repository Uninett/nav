<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<p><?php echo gettext("Hjelp"); ?></p>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();

echo "<p>" . gettext("Har du problemer med å få til noe med NAV webgrensesnittet skal du kunne finne hjelp her.");
echo '<p>[ <a href="">' . gettext("Last ned") . '</a> ] ' . gettext("brukermanual i PDF-format.");

?>
<h2><?php echo gettext('Introduksjon'); ?></h2>
<?php echo gettext('<p>Hei'); ?>
<h2><?php echo gettext('FAQ'); ?></h2>
<?php echo gettext('<p>Q: Foo<p>A: Bar'); ?>

</td></tr>
</table>
