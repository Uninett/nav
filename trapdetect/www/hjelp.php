<?php require('include.inc'); ?>

<?php tittel("TrapDetect") ?>

Hjelpsiden - for de trengende...

<?php topptabell(topp) ?>

<center><p><h2><u><b>TRAPDETECT</b></u></h2></p></center>

<p><h3>Bakgrunn:</h3></p>
Programmet er laget sommeren 2000, som et sommerprosjekt ved ITEA,
NTNU. Programmet er skrevet av John Magne Bredal, student ved NTNU,
Fakultet for Elektroteknikk og Telekommunikasjon, Linje for
Telematikk. 
<p>
I løpet av høsten er det kommet mer og mer forbedringer,
oppdateringer og bug-fikser, og jeg føler meg ennå ikke helt ferdig
med det. Vi har blant annet gått over til å bruke database i stedetfor
å la det være fil-basert og det er blitt mer og mer sentralt i NAV sitt
beskjedsendingsoppsett. De fleste programmene som vil sende ut mail
eller sms-meldinger på bakgrunn av hendelser bruker nå TrapDetect.
</p>

<p><h3>Hva gjør programmet:</h3></p>

<p> Programmet tar i mot traps vha. en snmptrap-daemon. Denne daemonen
lytter på port 162, som er default snmptrap-port, og snapper opp
eventuelle pakker som er adressert til den. Deretter leser den
innholdet i pakken og sender informasjonen videre til programmet.
</p>

<p> Programmet behandler deretter informasjonen som kommer inn. Det
reagerer på traps i henhold til ulike konfigurasjonsfiler, oppdaterer
filer og sender beskjeder via mail eller GSM. Nærmere detaljer vil jeg
ikke komme inn på her, da det er uvesentlig for bruk av
web-siden. Interesserte kan henvende seg til meg på adressen gitt
nederst på siden.  </p>

<p> Hensikten med dette er å få en oversikt over hva som skjer på
nettverket, og samtidig være en varslingsstasjon for de som drifter
det. Ved å spesifisere hvilke traps og hvilke enheter som det skal
reageres på, kan man luke ut det som er uviktig, og dermed slippe
unødvendig "støy". Hvis en enhet eller en link skulle gå ned, hvis det
er for mye last på linjene, eller hvis enheten nettopp har måttet
restarte, så vil man vite om det i løpet av få sekunder, og dermed
kunne reagere deretter.  </p>

<p><h3>Hva er "traps"?:</h3></p>

<p> En trap er en beskjed sendt via nettet fra en enhet vha. SNMP
(Simple Network Management Protocol).  Meningen med en trap er at den
skal inneholde statusinformasjon som enheten vil informere andre
enheter om. Derfor må det være noe som forårsaker at en trap sendes
ut. Dette konfigureres på hver enhet, og kan være alt fra at en bruker
logger av enheten, til at enheten foretar en restart.  </p>

<p> En trap må ha en mottaker for å ha mening. Eller, for å si det som
det egentlig er: en trap må snappes opp av noen for at den skal være
informativ. Det er dette TrapDetect gjør. Ved å bruke en nedlastet
snmptrap-daemon lytter det på port 162, og snapper opp traps
der. Deretter ser programmet på innholdet, og vurderer hva som skal
gjøres ut fra det.  </p>

<p> En stor del av informasjonen i en trap kommer fra OID'er (Object
IDentifier). En OID kan best sammenlignes med en unik tallrekke
adskilt av punktum som identifiserer informasjonen i
trap'en. F.eks. sier OID'en:<br> <b>.1.3.6.1.6.3.1.1.5.3</b><br> at
det er en linkDown-trap som er kommet inn. Hvis trap'en i tillegg
inneholder denne linjen:<br> <b>.1.3.6.1.2.1.2.2.1.1.18 18</b><br> så
vet man at det er interFaceIndex 18 som har gått ned.  Så ved å
identifisere alle OID'ene i en trap, kan man finne ut hva som skjer og
handle deretter.  </p>

<p>
Mer utfyllende informasjon om SNMP, traps o.l. kan du finne blant
annet her:<br>
<a href="http://www.pantherdig.com/snmpfaq/">SNMP-FAQ</a><br>
<a href="http://www.cisco.com/univercd/cc/td/doc/cisintwk/ito_doc/snmp.htm">CISCO</a><br>
</p>

<p><h3>Oversikt over menyvalg:</h3></p>

<ul>

<a name="status"><li><b><u>STATUS</u></b></a>

   <p> Status viser oversikt over sykmeldinger som er kommet inn fra
   enhetene ved NTNU. De innleggene som er her, er ikke blitt
   friskmeldt, og sier noe om potensielle problemer ved enhetene som
   har sendt meldingene.  </p>

   <p> Innleggene gir informasjon om når trap'en kom inn, fra hvilken
   enhet (navn og ip-adresse), og eventuell mer info.  </p>

<a name="hendelsesregister"><li><b><u>HENDELSESREGISTER</u></b></a>

   <p> Hendelsesregistret er en liste over de siste hendelsene som er
   registrert. I registret er det oversikt over alle traps som er
   kommet inn i løpet av det siste døgnet, med start klokken 2400 hver
   natt/kveld. Registret viser oversikt over sykmeldinger, og
   eventuelle friskmeldinger. I tillegg vises oversikt over såkalte
   tilstandsløse traps, dvs. traps som ikke har friskmelding. Et
   eksempel på slike er coldStart, en ren engangstrap som sier ifra om
   at enheten har foretatt en restart.  </p>

   <ul>
   <li><b><u>Dagens register</u></b>

   <p>Dagens register er en oversikt over hva som har skjedd fra
   klokken 24.00 og til nå. Friskmeldinger blir notert med dato under
   sykmeldingen. Ved søk kan man velge mellom følgende alternativer: </p>

   <ul>

   <li><u>Friskmeldte</u>: Dette er sykmeldinger som har blitt
    friskmeldt vha. av en tilsvarende friskmeldingtrap. Dette kan skje
    med de fleste traps, men ikke med alle. Se kommentar om
    tilstandsløse traps ovenfor.

    <li> <u>Sykmeldte</u>: Dette er generelle sykmeldinger som ikke er
    blitt friskmeldt. Dette kan ha to årsaker: ingen friskmelding er
    kommet inn eller det er en tilstandsløs trap som ikke kan få
    friskmelding. NB!  Antall sykmeldinger i hendelsesregistret kan da
    bli større enn antall sykmeldinger i status-oversikten. Dette er
    helt normalt.  <li><u>Begge</u>: Dette viser alle innlegg, både
    sykmeldinger og friskmeldinger.  </ul>

    <p> I tillegg kan man søke på det man vil ved å taste inn en
    tekststreng i det hvite feltet, og man kan søke på bestemte
    sykmeldinger ved å bruke drop-down-menyen til høyre. Denne menyen
    oppdaterer seg selv automatisk fra TrapDetect.conf-fila, og vil
    dermed ha fullstendig oversikt over mulige sykmeldinger.  </p>

    <p> NB! Alle søkefunksjoner kan brukes samtidig, så hvis man vil
    ha en oversikt over alle friskmeldinger, med søkeord bredal, med
    sykmelding hystereseAlarmOn, så er det fullt mulig.  </p>

    <li><b><u>Tidligere register</u></b>

    <p> Tidligere register gir deg mulighet til å se på de tidligere
    hendelsesregistrene som er lagret. Man vil ha nøyaktig de samme
    mulighetene for søk og oppslag som i Dagens register.  </p>

    <p> For å aksessere et tidligere register, skriv inn fra hvilken
    dato du vil ha oversikt over, og trykk Enter. Oversikten vil da
    komme opp. Datofeltet defaulter til gårdagens dato, men det er
    fullt mulig å skrive inn en annen dato. Hvis register for denne
    dagen ikke finnes, vil du få beskjed om det. Alle 6 tegn må
    skrives, så hvis du vil ha oversikt over 6 juli 2000, må du skrive
    060700.  </p>

</ul>

<a name="logg"><li><b><u>LOGG</u></b></a>
	<p>
	 Loggen er for det meste ikke interessant for den vanlige bruker. Den
	 inneholder en rå og ubehandlet oversikt over alle traps som er kommet
	 inn, både traps som programmet reagerer på og traps som programmet
	 overser. 
	</p>

	<p>
	 Det er imidlertid en del bruksområder når det gjelder loggen. For det
	 første har man en oversikt over alt som har skjedd. I tillegg er det
	 mulig å tyde de OID'ene som er kommet inn, og finne ut om det er
	 interessant info eller ikke. Et siste bruksområde er debugging av
	 programmet, siden output til loggen er skrevet av programmet alt etter
	 hvilke aksjoner det har gjort med de ulike traps.
	</p>

<ul>
	 <li><b><u>Dagens logg</u></b>
	 
	  <p> Dagens logg er en oversikt over alt som har kommet inn
	   til programmet siden klokken 24.00 samme dag og frem til
	   nå. Den viser klokkeslett trap'en kom inn og uptime, navn
	   og ip-adresse på enheten som sendte. I tillegg skrives alle
	   OID'er som er kommet inn med trap'en, og output fra
	   programmet.  </p>

	  <p> For å få litt mer oversikt, kan man søke på
	   tekststrenger i loggen. Skriv inn søkeord i det hvite
	   feltet og trykk Submit, evt. trykk Enter i tekstfeltet. Du
	   vil da få oversikt over alle innlegg med søkeordet i. For å
	   få oversikt over samtlige innlegg igjen, bare trykk på
	   linken til Dagens logg, eller null ut tekstfeltet og trykk
	   Submit.  </p>

	 <li><b><u>Tidligere logg</u></b>

	 <p> Tidligere logg gir deg mulighet til å se på de tidligere
	  loggene som er lagret. Man vil ha nøyaktig de samme
	  mulighetene for søk som i Dagens logg.  </p>

	 <p> For å aksessere en tidligere logg, skriv inn fra hvilken
	  dato du vil ha loggen, og trykk Enter. Loggen vil da komme
	  opp. Datofeltet defaulter til gårdagens dato, men det er
	  fullt mulig å skrive inn en annen dato. Hvis logg for denne
	  dagen ikke finnes, vil du få beskjed om det. Alle 6 tegn må
	  skrives, så hvis du vil ha oversikt over 6 juli 2000, må du
	  skrive 060700.  </p>

</ul>

<a name="statistikk"><li><b><u>STATISTIKK</u></b></a>
	
	<p> Statistikk inneholder en del oversikter som kan være både
	 nyttige og interessante. Statistikken består hovedsaklig av
	 to oversikter: en for antall traps mottatt pr. enhet, og en
	 for antall traps mottatt pr. OID.  </p>

<ul>	 <li><b><u>Generelt</u></b>

	 <p>Her vises en generell oversikt over alle traps som er
	 kommet inn, hvor mange av hver, fra hvilken enhet, hvor mange
	 totalt osv. Merk at dager tilbake sjelden overstiger
	 60. Dette fordi databasen dumpes hver måned, slik at det
	 første innslaget i databasen alltid er fra tidlig i forrige
	 måned.</p>

	 <li><b><u>Traps pr. enhet</u></b> 
     
         <p> Viser en grafisk oversikt over antall traps som er
	 mottatt fra hver enhet i en tidsperiode som velges av bruker
	 Denne blir fort stor, da det er mange forskjellige enheter
	 som sender traps til programmet. Meningen med denne
	 fremstillingen er å få god oversikt over hvilke enheter som
	 sender mest traps, og forholdet enhetene imellom.  </p>

	 <p> For hver søyle/enhet er det mulig å klikke seg inn på den
	 bestemte enheten og se detaljoversikt for hvilke traps den
	 har sendt ut. Data vil fremdeles være for det tidsrommet
	 brukeren valgte.</p>

	 <p> Videre er det også mulig å klikke videre enda et steg for
	 å få oversikt over de meldinger som er kommet inn. </p>

	<li><b><u>Traps inn</u></b>

	 <p> Viser en grafisk oversikt over antall traps som er
	 mottatt fra hver enhet i en tidsperiode som velges av bruker
	 Denne blir fort stor, da det er mange forskjellige enheter
	 som sender traps til programmet. Meningen med denne
	 fremstillingen er å få god oversikt over hvilke OID'er som
	 forekommer oftest, og forholdet OID'ene imellom.  </p>

	 <p> Som for de andre statistikkene er det mulig å trykke seg
	 inn på hver søyle og se på detaljoversikter. Her er det
	 oversikt over hvilke enheter som har sendt ut denne typen OID
	 i løpet av det valgte tidsrommet. </p>

	 <p> Videre er det også mulig å klikke videre enda et steg for
	 å få oversikt over de meldinger som er kommet inn. Se MERKNAD
	 ovenfor</p>

</ul>

<a name="diverse"><li><b><u>DIVERSE</u></b></a>
  <p>
    Herunder kommer det som ikke lar seg klassifisere under andre overskrifter.
  </p>
<ul>

   <li><b><u>Redigering av innlegg</b></u>

   <p>
    For å komme til denne linken må du ha administreringsadgang
    til sidene. Du vil bli spurt om brukernavn og passord for å komme
    inn. 
   </p>

   <p>
    Her kan du redigere innlegg. Du får en oversikt over nåværende
    status, og valg mellom å slette eller friskmelde innlegg. For å velge
    hvilke innlegg du vil redigere trykker du på knappen ved siden av
    innlegget. Når du har valgt alle innlegg du vil gjøre noe med,
    trykker du <i>Slett</i> eller <i>Friskmeld</i>, skriver inn navnet ditt for
    registrering og trykker Submit. 
   </p>

   <p>NB! Navnet ditt vil ikke ha noen
    betydning ved sletting av innlegg, bare ved friskmelding. Det vil da stå ved
    siden av friskmeldingen hvem som har friskmeldt innlegget.
   </p>

</ul>
</ul>

<p><h3>Referanser/Copyright:</h3></p>
<ul>
	<li>Dette systemet er gjort mulig vha:
	<ul>
		<li><a href="http://www.perl.com">PERL</a>
		<li><a href="http://ucd-snmp.ucdavis.edu/">UCD-SNMP -
		programpakke</a>
		<li><a href="http://www.php.net">PHP</a>
		<li><a href="http://www.linux.org">Linux</a>
		<li><a
		href="http://www.gnu.org/software/emacs/emacs.html">EMACS</a> - The only option
		<li>Kaffe - stoooore mengder
		<li>Folk og røvere på ITEA/Teknostallen som har kommet med gode
		råd og forslag.
	</ul>
</ul>

<p><h3>Spørsmål:</h3></p>

<p>Eventuelle spørsmål/klager/meninger kan rettes til meg
personlig:</p>
<p>
John Magne Bredal<br>
Tlf: 91 56 52 66<br>
Email: bredal@stud.ntnu.no<br>
</p>
<p>
Mest sannsynlig vil jeg ikke svare med mindre mailen kommer fra
ITEA-ansatte... :)
</p>

<?php bunntabell() ?>



