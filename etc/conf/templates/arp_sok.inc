<?php

# $Id: arp_sok.inc,v 1.2 2002/08/13 08:41:17 mortenv Exp $
#
# Denne filen skal ta inn vlan, og returnere en link eller ingenting.
# Dette avhenger av hvilket vlan som gis, 
# og hvilken tabell i arp_sok.php det skal brukes til 

# <tabell> er: 
# mac_cam  søk på mac i cam $svar(sysname,modul,port,mac,fra,til,vlan,ip)
# mac_arp  søk på mac i arp $svar(ip,mac,fra,til,vlan)
# ip_arp   søk på ip  i arp $svar(ip,mac,fra,til,vlan) 

# Hvordan bygge ut:
# Legg inn en ny if i funksjonen lenke - og det skal funke :)
# Legg merke til at man har mulighet til å legge ut link i tre
# forskjellige tabeller (som listet opp ovenfor).
#
# arp_sok.php tar høyde for dette, det som må editeres er denne fila.

function lenke($tabell,$svar)
{

$res = '';

if ($tabell == 'mac_cam')
{
  // Her kan du gjøre noe
}
elseif ($tabell == 'mac_arp')
{
  // Og her
}
elseif ($tabell == 'ip_arp')
{
  // Og her
}

return($res);

}
?>
