#!/bin/bash -xe

run_jstests() {
    /javascript-tests.sh
}

run_pylint() {
    time "/pylint.sh" > "${WORKSPACE}/pylint.txt"
}

dump_possibly_relevant_apache_accesses() {
    set +x
    ACCESSLOG="${BUILDDIR}/var/log/apache2-access.log"
    if [ -e "$ACCESSLOG" ]; then
        echo "Potentially relevant 40x errors from Apache logs:"
	echo "-------------------------------------------------"
	grep " 40[34] " "$ACCESSLOG"
	echo "-------------------------------------------------"
    fi
}


# MAIN EXECUTION POINT
cd "$WORKSPACE"
/build.sh

run_pylint &
/count-lines-of-code.sh &

# Run unit tests before starting services
/python-unit-tests.sh

# start services
/create-db.sh
/start-services.sh
trap dump_possibly_relevant_apache_accesses EXIT

# Run integrations tests after everything is up
/integration-tests.sh
/functional-tests.sh

run_jstests


echo "Waiting for background tasks to end"
wait

echo "test.sh done"
