#!/bin/sh
#
# This script should be invoked under VM and it's postgres user.
#
# See tools/vagrant-provision.sh for flow.


alternative() {
  echo "syncdb.py -c probably failed due to existing database user or database"
  echo "You could always use this oneliner to run syncdb.py without user/database creation:"
  echo ""
  echo "vagrant ssh -c 'source ~vagrant/.env/bin/activate && /vagrant/sql/syncdb.py'"
  echo ""
  exit 0
}

. ~vagrant/.env/bin/activate
export PYTHONPATH="/vagrant/python"
/vagrant/sql/syncdb.py -c || alternative
