<?php

require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');
if (!$bruker) {
  $bruker = $PHP_AUTH_USER;
}
navstart("Rapporter",$bruker);
?>


<h1>Rapporter</h1>
 
<ul>
<li> <a href="/ragen/?rapport=boks"> Utstyrsregister</a> (alt
utstyr)
  <ul>
  <li> <a href="/ragen/?rapport=gw"> Kun rutere (GW)</a>
  <li> <a href="/ragen/?rapport=sw"> Kun svitsjer (SW)</a>
  <li> <a href="/ragen/?rapport=kant"> Kun kantutstyr (KANT)</a>
  <li> <a href="/ragen/?rapport=srv"> Kun servere (SRV)</a>
  <li> <a href="/ragen/?rapport=oppsop"> Resten</a>
  </ul>
<li> <a href="/ragen/?rapport=gwport"> Ruterporter</a> og
     <a href="/ragen/?rapport=prefiks"> brukte prefiks</a>
<li> <a href="/ragen/?rapport=swportv"> Svitsjeporter</a>, kun
     <a href="/ragen/?rapport=swportt"> svitsjeporter som er trunk</a>
<li> <a href="/ragen/?rapport=modules"> moduler</a>,
     <a href="/ragen/?rapport=mem"> minne/flash</a>
<li> <a href="/ragen/?rapport=rom"> Rom</a>
<li> <a href="/ragen/?rapport=sted"> Sted</a>
<li> <a href="/ragen/?rapport=org"> Organisasjon</a>
 
 
</ul>

<?php
navslutt();
?>