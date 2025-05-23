#!groovy

def schedule = env.BRANCH_NAME == 'master'       ? '@weekly' :
               env.BRANCH_NAME == 'release_3.0'  ? "@weekly" : ''


pipeline {
  agent {label 'rhel8'}

  triggers {
    // trigger builds per schedule
    cron(schedule)
  }

  environment {
    PATH = "/home/gbors/pythonversions/3.8/bin:${PATH}"
  }

  stages {
    stage('Init') {
      steps {
        lastChanges(
          since: 'LAST_SUCCESSFUL_BUILD',
          format:'SIDE',
          matching: 'LINE'
        )
      }
    }

    stage('UnitTest') {
      steps {
        sh '''
          ./RunAllUnitTests
        '''
        junit '**/results-*.xml'
      }
    }
    stage('IntegrationTest') {
      steps {
        sh '''
          ./RunAllIntegrationTests
        '''
        junit '**/results-*.xml'
      }
    }
  }

  post {
    always {
      do_notify()
    }
  }
}
