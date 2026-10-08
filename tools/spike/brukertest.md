# Brukertester av de nye grafene

NAV skal bytte ut Rickshaw med Chart.js (#3967). Før vi starter vil vi gjøre en enkel brukertest. Denne veiledningen hjelper deg på vei.

## Test-kode og url-parametre

Test-koden ligger i greina `spike/rickshaw-replacement`. En URL-parameter slår på visning av grafene:

| URL-parameter | Hva siden viser |
|---|---|
| ingen | Rickshaw |
| `?graphlib=chartjs` | Chart.js |
| `?graphlib=rickshaw&graphlib=chartjs` | Rickshaw og Chart.js ved siden av hverandre |
| `?graphlib=all` | Rickshaw, uPlot og Chart.js ved siden av hverandre |

På sider med en `#`-del står parameteren foran: `/search/room/100/?graphlib=chartjs#!sensors`.

Det er laget script for å fylle Graphite med testdata for testsidene.

## Oppsett

Gjør dette i NAVs devcontainer.

1. **Kopier databasen.** Se "migrating_prod_db_to_dev" i NAV-dokumentasjonen. Det er lenket fra `doc/hacking/using-devcontainers.rst`.

   ```sh
   tools/reset-db-from-remote.sh <bruker>@<vk>
   ```

   Har du fått en dumpfil fra noen, kjører du `zcat <fil>.sql.gz | tools/restore-db.sh` i stedet.

2. **Sjekk ut `spike/rickshaw-replacement`, og bygg CSS-en.** Skriptene for testdata ligger i `tools/spike/` på den grenen.

   ```sh
   git checkout spike/rickshaw-replacement
   make sassbuild
   ```

3. **Start webgrensesnittet** med `uv run django-admin runserver`.

4. **Fyll Graphite med testdata.** Kjør skript for det du ønsker å se på (husk ID)

NB: Det er bare et utvalg av sider som bruker disse dataene, se "Testsider".

   ```sh
   uv run python tools/spike/mock_port_metrics.py <id>
   uv run python tools/spike/mock_room_sensors.py <id>
   uv run python tools/spike/mock_vlan_prefixes.py <id>
   ```

   Hvert skript tar en ID som argument, slik at du kan fylle data for et annet interface, rom eller VLAN.

## Testsider

| Side | Adresse |
|---|---|
| Portmålinger | `/ipdevinfo/<utstyr med interface>/interface=<pk>/` |
| Sensorer i et rom | `/search/room/<romid>/#!sensors` |
| Sensordetaljer | `/ipdevinfo/sensor/<sensorid>` |
| VLAN-detaljer | `/search/vlan/<pk>/` |
| Dashbord | `/?graphlib=chartjs` |

## Gjennomføring

- Åpne siden med `?graphlib=rickshaw&graphlib=chartjs`. `?graphlib=all` viser alle tre.
- Vurder å sammenligne med prod hos de du intervjuer.
- Hold musen over grafen for å se verdiene.
- Klikk på en serie i forklaringen for å skjule eller vise den, og hold musen over den for å framheve serien.
- Dra over en graf for å zoome inn, og dobbeltklikk for å zoome ut igjen.
- Hold inne Shift og dra for å flytte en zoomet graf sidelengs.
- Gjør nettleservinduet smalere og bredere for å se hvordan grafene tilpasser seg. Det er ikke lagt til noen stacking av selve grafene, så det blir jo fort fullt med alle tre grafene på siden.

## Brukertest grafer

### Innledning

NAV skal bytte til nytt system for å vise frem grafer. Dette fordi det gamle systemet ikke lenger blir vedlikehold og vi opplever feil og sikkerhetsproblemer i det.

Dette er en stor endring i noe som er viktig for mange, og for å være sikker på at dette fungerer på første forsøk vil vi gjerne ta en prat om dette.

Det vil være endringer i hvordan grafene ser ut og i funksjonaliteten i grafene. Bortsett fra det blir alt likt.

For å undersøke hvordan dette vil påvirke deg har vi hentet data fra din verktøykasse (kanksje?) og lagt til de nye grafene ved siden av de gamle. Slik kan vi sammenligne og få tilbakemelding om hva du synes.

### Spørsmål

- hvilke sider er det du bruker mest (i kontekst av grafer)
- hvilken funksjonalitet i grafene er det du bruker (vent på svar her)
    - bruke sliders for å velge tidsrom
    - når du har valgt tidsrom: flytte tidsrommet (panorere i grafen)
    - velge en av flere datasett
    - bruke musen for å se på dataene (hover for tooltip)
    - annet?
- er det noe du savner
- hva synes du om fargene
- hva synes du om størrelsen på skriften?
- resize og se hva som skjer (har dere tilfeller av veldig lange titler på grafene)
  - eks. på subtitle (**bare ChartJS**): search/vlan/5697679/?graphlib=all

NB: sparklines og gauges er ikke en del av disse endringene.

## Notater

Kopier denne delen for hver test.

- **Dato og bruker:**
- **Sidene brukeren bruker mest:**
- **Graffunksjoner brukeren bruker:**
- **Hva brukeren savnet:**
- **Farger:**
- **Skriftstørrelse:**
- **Endring av vindusstørrelse og lange titler:**
- **Andre kommentarer:**
