#!/bin/bash


#---------- Oppretter kataloger ----------

#
mkdir /usr/local/nav/local
mkdir /usr/local/nav/local/etc
mkdir /usr/local/nav/local/etc/conf
mkdir /usr/local/nav/local/etc/conf/live
mkdir /usr/local/nav/local/etc/conf/varsel
mkdir /usr/local/nav/local/etc/kilde

mkdir /usr/local/nav/local/log
mkdir /usr/local/nav/local/log/live
mkdir /usr/local/nav/local/log/varsel
mkdir /usr/local/nav/local/log/trapdetect
mkdir /usr/local/nav/local/log/cam

mkdir /usr/local/nav/local/cricket

mkdir /usr/local/nav/local/apache
mkdir /usr/local/nav/local/apache/htpasswd

mkdir /usr/local/nav/local/apache/pic
mkdir /usr/local/nav/local/apache/pub
mkdir /usr/local/nav/local/apache/res
mkdir /usr/local/nav/local/apache/sec
mkdir /usr/local/nav/local/apache/vhtdocs

mkdir /usr/local/nav/pg_backup

#---------- Installerer programmer ----------



#---------- Oppretter symbolinker ----------


#---------- Kopierer på plass config filer ---------

# kopierer på plass configfilen for backup programmet til postgres databasen
echo "*********************************************************************"
echo "* Huske å sette root passord og brukernavn for postgres databasen i  *"
echo "* /usr/local/nav/local/etc/conf/pgpasswd.conf. Denne filen burde kun *"
echo "* root ha mulighet til å lese                                        *"
echo "**********************************************************************"
cp /usr/local/nav/navme/setup/kilde/pgpasswd.conf /usr/local/nav/local/etc/conf/
chmod 600 /usr/local/nav/local/etc/conf/pgpasswd.conf
chown root.nav /usr/local/nav/local/etc/conf/pgpasswd.conf


