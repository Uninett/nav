#!groovy
/**
 * Work in tandem with tests/docker/Dockerfile & Co to run a full CI run in
 * Jenkins.
*/
def lastStage = ''
def requirementsChanged = false
node {
  setDisplayNameIfPullRequest()

  stage("Checkout") {
      lastStage = env.STAGE_NAME
      def scmVars = checkout scm
      requirementsChanged = sh(
                               returnStatus: true,
                               script: "git diff --name-only ${scmVars.GIT_PREVIOUS_SUCCESSFUL_COMMIT} ${scmVars.GIT_COMMIT} | egrep '^(tests/)?requirements.*txt\$'") == 0
  }

  try {
    def dockerfile = 'tests/docker/Dockerfile'

    def acceptableName = "${env.JOB_NAME}".replaceAll('/', '-').replaceAll('%2f', '-').replaceAll('%2F', '-')
    echo "Acceptable image name: ${acceptableName}"
    def imageTag = "nav/${acceptableName}:${env.BUILD_NUMBER}".toLowerCase()
    echo "Docker image tag: ${imageTag}"
    docker.build("${imageTag}", "-f ${dockerfile} .").inside("--tmpfs /var/lib/postgresql --volume ${WORKSPACE}:/source:rw,z --volume ${HUDSON_HOME}/.cache:/source/.cache:rw,z") {
        env.WORKSPACE = "${WORKSPACE}"

        stage("Prepare build") {
            lastStage = env.STAGE_NAME
            sh "env"  // debug print environment
            sh "git fetch --tags" // seems tags arent't cloned by Jenkins :P
            sh "rm -rf ${WORKSPACE}/reports/*"  // remove old, potentially stale reports
            if (requirementsChanged) {
              echo '============================= Some requirements files changed, recreating tox environments ============================='
              sh "tox --recreate --notest"
            }
        }

        try {
            def toxEnvirons = sh(returnStdout: true,
                                 script: "tox -a tox -a | egrep '^(unit|integration|functional|javascript|docs)' | paste -sd ,").trim().split(',')
            echo "Found these tox environments: ${toxEnvirons}"
            for (int i = 0; i < toxEnvirons.length; i++) {
                stage("Tox ${toxEnvirons[i]}") {
                    lastStage = env.STAGE_NAME
                    ansiColor('xterm') {
                        sh "tox -e ${toxEnvirons[i]}"
                    }
                }
            }

        } finally {
            junit "reports/**/*-results.xml"
            step([$class: 'CoberturaPublisher', coberturaReportFile: 'reports/**/*coverage.xml'])
        }

        stage("PyLint") {
            lastStage = env.STAGE_NAME
            sh "tox -e pylint"
            step([
                $class                     : 'WarningsPublisher',
                parserConfigurations       : [[
                                              parserName: 'PYLint',
                                                pattern   : 'reports/pylint.txt'
                                            ]],
                unstableTotalAll           : '1680',
                failedTotalAll             : '1730',
                usePreviousBuildAsReference: true
            ])
        }

        stage("Lines of code") {
            lastStage = env.STAGE_NAME
            sh "/count-lines-of-code.sh"
            sloccountPublish encoding: '', pattern: 'reports/cloc.xml'
        }

    }

    stage("Publish documentation") {
      lastStage = env.STAGE_NAME
      // publish dev docs and stable branch docs, but nothing else
      if (env.JOB_BASE_NAME == 'master' || env.JOB_BASE_NAME.endsWith('.x') || env.JOB_BASE_NAME == 'doctest') {
        // Archive documentation as an artifact to be copied from the doc publisher job
        sh "cd build/sphinx ; tar cvzf nav-docs.tar.gz html/"
        archiveArtifacts artifacts: 'build/sphinx/nav-docs.tar.gz', fingerprint: true

        echo "Triggering doc publishing job"
        build job: 'Publish NAV documentation', wait: false, parameters: [[$class: 'StringParameterValue', name: 'ParentJobName', value: env.JOB_NAME]]
      } else {
        echo "Not triggering doc publisher job for this branch"
      }
    }

} catch (e) {
    currentBuild.result = "FAILED"
    echo "Build FAILED set status ${currentBuild.result} in ${lastStage}"
    throw e
} finally {

    def testReports = sh (
        script: 'cd reports; find . -name "*-report.html" | paste -sd ,',
        returnStdout: true
    ).trim()
    echo "Found test reports: ${testReports}"
    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports', reportFiles: testReports, reportName: 'HTML test reports'])

    notifyBuild(currentBuild.result, lastStage)

  }
}



def notifyBuild(String buildStatus = 'STARTED', lastStage = 'N/A') {
  // build status of null means successful
  buildStatus =  buildStatus ?: 'SUCCESS'

  // Default values
  def colorName = 'RED'
  def colorCode = '#FF0000'
  def subject = "*${buildStatus}*: *`<${env.BUILD_URL}|${env.JOB_NAME}>` #${env.BUILD_NUMBER}*"
  def summary = "${subject} _(${currentBuild.rawBuild.project.displayName})_"
  def testStatus = ''

  // Override default values based on build status
  if (buildStatus == 'STARTED') {
    color = 'YELLOW'
    colorCode = '#FFFF00'
  } else if (buildStatus == 'SUCCESS') {
    color = 'GREEN'
    colorCode = '#00FF00'
  } else {
    color = 'RED'
    colorCode = '#FF0000'
    testStatus += "Failed in stage: _${lastStage}_\n"
  }

  testStatus += testStatuses()
  // Send notifications
  slackSend (color: colorCode, message: "${summary}\n${testStatus}")

}

import hudson.tasks.test.AbstractTestResultAction

@NonCPS
def testStatuses() {
    def testStatus = ""
    AbstractTestResultAction testResultAction = currentBuild.rawBuild.getAction(AbstractTestResultAction.class)
    if (testResultAction != null) {
        def total = testResultAction.totalCount
        def failed = testResultAction.failCount
        def skipped = testResultAction.skipCount
        def passed = total - failed - skipped
        testStatus = "*Tests*\nPassed: ${passed}, Failed: ${failed} ${testResultAction.failureDiffString}, Skipped: ${skipped}"

    }
    return testStatus
}

def setDisplayNameIfPullRequest() {
    if (env.BRANCH_NAME.startsWith('PR')) {
        def resp = httpRequest url: "https://api.github.com/repos/Uninett/nav/pulls/${env.BRANCH_NAME.substring(3)}"
        def ttl = getTitle(resp)
        def itm = getItem(env.BRANCH_NAME)
        itm.setDisplayName("${env.BRANCH_NAME} ${ttl}")
    }
}

@NonCPS
def getItem(branchName) {
    return Jenkins.instance.getItemByFullName("nav-pipeline/${branchName}")
}

@NonCPS
def getTitle(json) {
    def slurper = new groovy.json.JsonSlurper()
    def jsonObject = slurper.parseText(json.content)
    return jsonObject.title
}

// Local Variables:
// indent-tabs-mode: nil
// tab-width: 4
// End:
