<?php

require('/usr/local/nav/navme/apache/vhtdocs/nav.inc');
if (!$bruker) {
  $bruker = $PHP_AUTH_USER;
}
navstart("Rapporter",$bruker);
?>


<h1>Rapporter</h1>
 
<ul>
<li> <a href="/res/ragen/?rapport=netbox"> Utstyrsregister</a> (alt
utstyr)
  <ul>
  <li> <a href="/res/ragen/?rapport=type"> Liste over utstyrstyper</a>
  <li> <a href="/res/ragen/?rapport=gw"> Kun rutere (GW/GSW)</a>
  <li> <a href="/res/ragen/?rapport=sw"> Kun svitsjer (SW/GSW)</a>
  <li> <a href="/res/ragen/?rapport=netbox&kat=KANT"> Kun kantutstyr 
(KANT)</a>
  <li> <a href="/res/ragen/?rapport=wlan"> Kun trådløst (WLAN)</a>
  <li> <a href="/res/ragen/?rapport=srv"> Kun servere (SRV)</a>
  <li> <a href="/res/ragen/?rapport=servicemon"> Tjenester som overvåkes </a>
  <li> <a href="/res/ragen/?rapport=oppsop"> Resten</a>
  </ul>
<li> 
     <a href="/res/ragen/?rapport=prefix"> Brukte subnett 
/ prefiks / vlan</a>. Liste over 
<a href="/res/ragen/?rapport=gwport"> ruterporter</a>.
<li> <a href="/res/ragen/?rapport=swportv"> Svitsjeporter</a>, kun
     <a href="/res/ragen/?rapport=swportt"> svitsjeporter som er trunk</a>
<li> 
<a href="/res/ragen/?rapport=modultype"> modultyper</a>,
<a href="/res/ragen/?rapport=modules"> moduler</a>,
     <a href="/res/ragen/?rapport=mem"> minne/flash</a>
<li> <a href="/res/ragen/?rapport=room"> Rom</a>,
 <a href="/res/ragen/?rapport=location"> Sted</a>
<li> <a href="/res/ragen/?rapport=org"> Organisasjon</a>,
 <a href="/res/ragen/?rapport=usage"> Anvendelsestyper for subnett</a>
 
 </ul>

<h3>Snarveier</h3>

<b>Søk etter:</b>
<table>
<tr>
  <form action="./?rapport=netbox" method=POST>
  <td>utstyr i telematikkrom:</td>
  <td><input type=text name=roomid size=15></td>
  <td><input type=submit value="Søk"></td>
  </form>
</tr>
<tr>
  <form action="./?rapport=netbox" method=POST>
  <td>ip-adresse (% wildcard):</td>
  <td><input type=text name=host(ip) size=15></td>
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
