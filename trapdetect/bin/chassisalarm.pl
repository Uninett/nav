#!/usr/bin/perl
# Spesifikt script som tar seg av chassisAlarm-trap
# Kan brukes som eksempel for andre script.

chomp ($date = `date +%D-%T`);

# Disse tre verdiene kommer alltid først:
# OID er den OID'en som bestemmer hvilken trap det er.
$oid = shift;
$name = shift;
$ip = shift;

# OID'er som beskriver trap'en
$tempAlarm = ".1.3.6.1.4.1.9.5.1.2.13";
$fanStatus = ".1.3.6.1.4.1.9.5.1.2.9";
$powerOne = ".1.3.6.1.4.1.9.5.1.2.4";
$powerTwo = ".1.3.6.1.4.1.9.5.1.2.7";

# Bruker disse verdiene for å sjekke om den er syk eller ikke.
$chassisalarmOn = ".1.3.6.1.4.1.9.5.0.5";
$chassisalarmOff = ".1.3.6.1.4.1.9.5.0.6";

# HUSK: Fast oppsett på andre innlegg (push) er at navn, ip og beskrivelse MÅ være med.
# Første innlegg bør være dato...
# Beskrivelsen må være bokstavrett den som står i TrapDetect.conf
# Dette fordi innlegget skal fjernes fra syk-fila, og da må man ha noe å 
# søke på...
# Kan gjøres noe med etterhvert... :)
#  if ($oid eq $chassisalarmOn) {
#      push @beskjed, "$date\nMottatt trap fra $name, $ip: chassisAlarmOn";
#  } elsif ($oid eq $chassisalarmOff) {
#      push @beskjed, "$date\nMottatt trap fra $name, $ip: chassisAlarmOff";
#  } else {
#      print "Ukjent alarm\n";
#  }

# Parrer input
# Input kommer slik: OID=verdi
for (@ARGV) {
    if (/$tempAlarm/) {
	@temp = split /=/, $_;
    } elsif (/$fanStatus/) {
	@fan = split /=/, $_;
    } elsif (/$powerOne/) {
	@powerone = split /=/, $_;
    } elsif (/$powerTwo/) {
	@powertwo = split /=/, $_;
    }
}

##################################################
# Skjønnhetsmessig er det greit å ikke ha newline
# på hver push, evt. annen listeoperasjon.
# Det vil føre til en ekstra newline i output fra
# hovedprogrammet.
##################################################

# Sjekker de forskjellige verdiene.
# 1 = off, 2 = on, 3 = critical
if ($temp[1] == 1) {
    # Do nothing.
} elsif ($temp[1] == 2) {
    push @beskjed, "TempAlarm on";
    push @beskjed, 2;
} elsif ($temp[1] == 3) {
    push @beskjed, "TempAlarm critical!";
    push @beskjed, 1;
}

# 1 = other, 2 = ok, 3 = minor, 4 = major
if ($fan[1] == 1) {
    push @beskjed, "Fan unknown failure";
    push @beskjed, 2;
} elsif ($fan[1] == 2) {
    # Do nothing.
} elsif ($fan[1] == 3) {
    push @beskjed, "Fan minor failure";
    push @beskjed, 2;
} elsif ($fan[1] == 4) {
    push @beskjed, "Fan major failure";
    push @beskjed, 1;
} 

# 1 = other, 2 = ok, 3 = minor, 4 = major
if ($powerone[1] == 1) {
    push @beskjed, "Power1 unknown failure";
    push @beskjed, 2;
} elsif ($powerone[1] == 2) {
    # Do nothing 
} elsif ($powerone[1] == 3) {
    push @beskjed, "Power1 minor failure";
    push @beskjed, 2;
} elsif ($powerone[1] == 4) {
    push @beskjed, "Power1 major failure";
    push @beskjed, 1;
}

if ($powertwo[1] == 1) {
    push @beskjed, "Power2 unknown failure";
    push @beskjed, 2;
} elsif ($powertwo[1] == 2) {
    # Do nothing.
} elsif ($powertwo[1] == 3) {
    push @beskjed, "Power2 minor failure";
    push @beskjed, 2;
} elsif ($powertwo[1] == 4) {
    push @beskjed, "Power2 major failure";
    push @beskjed, 1;
}

# Beskjeden skrives ut slik som man vil, men innlegget med navn, ip og beskrivelse må komme først.
# I tillegg er det et krav at alarmen kommer sist. 
# Alarm bør settes!
# NB! Alarm = 0 => ingen alarm sendes.
# NB! For å bruke standard alarm, sett alarm til '999'.
# F.eks. push @beskjed, "999";

for (@beskjed) {
    print "$_\n";
}
