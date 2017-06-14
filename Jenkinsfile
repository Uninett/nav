#!groovy
// Work in tandem with tests/docker/Dockerfile & Co to run a full CI run in
// Jenkins.
// TODO: SLOCCount plugin doesn't support publishing results in pipelines yet.
// TODO: Publish coverage data
node {
    stage("Checkout") {
	checkout scm
    }
    
    docker.build("nav/testfjas:${env.BUILD_NUMBER}", "-f tests/docker/Dockerfile .").inside() {
        env.WORKSPACE = "${WORKSPACE}"
        env.BUILDDIR = "/opt/nav"
        env.TARGETURL = "http://localhost:8000/"

        stage("Build NAV") {
            sh "/build.sh"
        }
        
        parallel(
            "analyze": {
                stage("Analyze") {
                    parallel (
                        "PyLint": {
                            env.PYLINTHOME = "${WORKSPACE}"
                            sh """/pylint.sh > "${WORKSPACE}/pylint.txt" """
                            //sh 'cat pylint.txt'
                            step([
                                $class                     : 'WarningsPublisher',
                                parserConfigurations       : [[
                                                              parserName: 'PYLint',
                                                                pattern   : 'pylint.txt'
                                                            ]],
                                unstableTotalAll           : '1650',
                                failedTotalAll             : '1700',
                                usePreviousBuildAsReference: true
                            ])

                        },
                        "Lines of code": {
                            sh "/count-lines-of-code.sh"
                        }
                    )
                }
            },
            "test": {
	        try {
		    stage("Run Python unit tests") {
			sh "/python-unit-tests.sh"
		    }

		    stage("Create database and start services") {
			sh "/create-db.sh"
			sh "/start-services.sh"
		    }

		    stage("Run integration tests") {
			sh "/integration-tests.sh"
		    }

		    stage("Run Selenium tests") {
			sh "/functional-tests.sh"
		    }

		    stage("Run JavaScript tests") {
			sh "/javascript-tests.sh"
		    }
		} finally {
                    junit "**/*-results.xml"
		}
            }
        )

    }
    
    stage("Publish documentation") {
        if (env.JOB_NAME == 'master') {
            VERSION = sh (
                script: 'cd ${WORKSPACE}/doc; python -c "import conf; print conf.version"',
                returnStdout: true
            ).trim()
            echo "Publishing docs for ${VERSION}"
            sh 'rsync -av --delete --no-perms --chmod=Dog+rx,Fog+r "${WORKSPACE}/doc/html/" "doc@nav.uninett.no:/var/www/doc/${VERSION}/"'
        }
    }

    archiveArtifacts artifacts: 'tests/*-report.html'

}
