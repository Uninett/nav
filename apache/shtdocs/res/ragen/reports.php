<?php

require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');
if (!$bruker) {
  $bruker = $PHP_AUTH_USER;
}
navstart("Rapporter",$bruker);
?>


<h1>Rapporter</h1>
 
<ul>
<li> <a href="/res/ragen/?rapport=boks"> Utstyrsregister</a> (alt
utstyr)
  <ul>
  <li> <a href="/res/ragen/?rapport=gw"> Kun rutere (GW)</a>
  <li> <a href="/res/ragen/?rapport=sw"> Kun svitsjer (SW)</a>
  <li> <a href="/res/ragen/?rapport=kant"> Kun kantutstyr (KANT)</a>
  <li> <a href="/res/ragen/?rapport=srv"> Kun servere (SRV)</a>
  <li> <a href="/res/ragen/?rapport=oppsop"> Resten</a>
  <li> <a href="/res/ragen/?rapport=type"> Liste over utstyrstyper</a>
  </ul>
<li> <a href="/res/ragen/?rapport=gwport"> Ruterporter</a> og
     <a href="/res/ragen/?rapport=prefiks"> brukte prefiks</a>
<li> <a href="/res/ragen/?rapport=swportv"> Svitsjeporter</a>, kun
     <a href="/res/ragen/?rapport=swportt"> svitsjeporter som er trunk</a>
<li> <a href="/res/ragen/?rapport=modules"> moduler</a>,
     <a href="/res/ragen/?rapport=mem"> minne/flash</a>
<li> <a href="/res/ragen/?rapport=rom"> Rom</a>
<li> <a href="/res/ragen/?rapport=sted"> Sted</a>
<li> <a href="/res/ragen/?rapport=org"> Organisasjon</a>
<li> <a href="/res/ragen/?rapport=anv"> Anvendelsestyper for subnett</a>
 
 </ul>

<h3>Snarveier</h3>

<b>Søk etter:</b>
<table>
<tr>
  <form action="./?rapport=boks" method=POST>
  <td>utstyr i telematikkrom:</td>
  <td><input type=text name=romid size=15></td>
  <td><input type=submit value="Søk"></td>
  </form>
</tr>
<tr>
  <form action="./?rapport=prefiks" method=POST>
  <td>nettadresse (ikke wildcard):</td> 
  <td><input type=text name=nettadr size=15></td>
  <td><input type=submit value="Søk"></td>
  </form>
</tr>
<tr>
  <form action="./?rapport=swportv" method=POST>
  <td>utbredelse av vlan (ikke wildcard):</td>
  <td><input type=text name=vlan size=15></td>
  <td><input type=submit value="Søk"></td>
  </form>
</tr>
</table>

<?php

navslutt();
?>
